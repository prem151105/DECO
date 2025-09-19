import os
import json
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt

from src.document_processor import DocumentProcessor
from src.gemini_analyzer import GeminiAnalyzer, GeminiUnavailable
from src.knowledge_graph import KnowledgeGraphGenerator
from src.compliance_monitor import ComplianceMonitor
from src.storage import Storage
from src.analyzer_router import AnalyzerRouter
from src.email_integration import EmailIntegration
from src.advanced_search import AdvancedSearch

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(title="DocSense AI API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
BASE_DIR = Path(__file__).parent
processor = DocumentProcessor()
kg = KnowledgeGraphGenerator()
compliance = ComplianceMonitor()
storage = Storage(str(BASE_DIR))
router = AnalyzerRouter("gemini")
email_integration = EmailIntegration()
advanced_search = AdvancedSearch()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "employee"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DocumentUpload(BaseModel):
    recipients: List[int]  # user IDs

class SearchQuery(BaseModel):
    query: str
    search_type: str = "hybrid"
    filters: Optional[Dict[str, Any]] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        # Get full user info
        users = storage.get_users()
        user = next((u for u in users if u["username"] == username), None)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Routes
@app.post("/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user exists
    if storage.authenticate_user(user.username, ""):  # Just check username
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    storage.create_user(user.username, user.email, hashed_password, user.role)
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    hashed_password = get_password_hash(user.password)
    db_user = storage.authenticate_user(user.username, hashed_password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"sub": db_user["username"], "role": db_user["role"], "user_id": db_user["id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users")
async def get_users(current_user: dict = Depends(get_current_admin)):
    return storage.get_users()

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    recipients: str = Form(...),  # JSON string of user IDs
    current_user: dict = Depends(get_current_admin)
):
    # Parse recipients
    try:
        recipient_ids = json.loads(recipients)
    except:
        raise HTTPException(status_code=400, detail="Invalid recipients format")
    
    # Read file
    content = await file.read()
    meta = processor.extract_metadata(file.filename, content)
    quick = processor.quick_skim(content, meta)
    
    llm = None
    if router.ready:
        llm = router.analyze(content, role=meta.get("suggested_role", "manager"))
    
    compliance_flags = compliance.check(meta, quick, llm)
    
    # Save document
    fulltext = processor.extract_fulltext(content, meta.get("ext", ""))
    fhash = processor.file_hash(content)
    doc_id = storage.save_document(
        filename=file.filename,
        file_hash=fhash,
        meta=meta,
        quick=quick,
        llm=llm,
        compliance=compliance_flags,
        fulltext=fulltext,
    )
    
    # Index for search
    advanced_search.index_document(str(doc_id), file.filename, fulltext, meta)
    
    # Save recipients
    storage.save_recipients(doc_id, recipient_ids)
    
    # Send emails
    if email_integration.email_ready:
        users = storage.get_users()
        recipient_emails = [u["email"] for u in users if u["id"] in recipient_ids]
        summary = quick.get("summary", "Document processed")
        email_integration.route_document({
            "filename": file.filename,
            "metadata": meta,
            "quick_view": quick,
            "llm_analysis": llm,
        }, recipient_emails)
    
    return {"doc_id": doc_id, "message": "Document processed and distributed"}

@app.post("/search")
async def search_documents(
    search: SearchQuery,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == "admin":
        results = advanced_search_query(search.query, search.search_type, json.dumps(search.filters or {}))
    else:
        # For employees, only search their documents
        user_docs = storage.get_user_documents(current_user["id"])
        # Filter by query - simplified
        results = [d for d in user_docs if search.query.lower() in d["filename"].lower() or search.query.lower() in json.dumps(d).lower()]
    
    return results

@app.get("/my-documents")
async def get_my_documents(current_user: dict = Depends(get_current_user)):
    # Need user id - assume we can get it from username
    users = storage.get_users()
    user = next((u for u in users if u["username"] == current_user["username"]), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return storage.get_user_documents(user["id"])

# Helper function for search
def advanced_search_query(query: str, search_type: str = "hybrid", filters: str = "") -> List[Dict[str, Any]]:
    if search_type == "full_text":
        results = advanced_search.full_text_search(query)
    elif search_type == "semantic":
        results = advanced_search.semantic_search(query)
    else:
        results = advanced_search.hybrid_search(query)
    
    if filters:
        try:
            filter_dict = json.loads(filters)
            results = advanced_search.filter_by_metadata(filter_dict, results)
        except:
            pass
    
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)