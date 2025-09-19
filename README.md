# KMRL Knowledge Engine - DocSense AI Platform

**Complete Implementation of KMRL's Strategic Blueprint for Knowledge-Centric Enterprise**

This is a comprehensive implementation of the KMRL Knowledge Engine as described in the strategic blueprint. It transforms KMRL into a knowledge-centric organization through:

## Four-Pillar Implementation

### Pillar I: Unified Knowledge Platform
- Federated, metadata-driven architecture
- Seamless integration with existing systems (Maximo, SharePoint simulation)
- Single source of truth for all enterprise data

### Pillar II: Intelligent Document Processing
- OCR for images, PDFs, and scanned documents
- Advanced NLP and ML for document classification and entity recognition
- Multilingual support (English/Malayalam/Bilingual)
- AI-powered translation capabilities
- Specialized parsers for complex data types

### Pillar III: Enterprise Data Integration
- Unified Namespace (UNS) simulation for real-time data
- IoT condition monitoring integration
- Maximo work order linking
- SharePoint document metadata integration

### Pillar IV: Cultural Transformation
- Automated notifications and routing
- Role-based analysis and distribution
- Cross-departmental awareness tools

## Features
- **Document Processing**: PDFs, DOCX, images with OCR
- **Multilingual Support**: English, Malayalam, and bilingual detection
- **Advanced Search**: Full-text, semantic, and hybrid search with metadata filtering
- **Knowledge Graph**: Interactive visualization of entities and relationships
- **Compliance Monitoring**: Automatic flagging for CMRS, safety, procurement
- **Real-Time Data Integration**: UNS simulation with live sensor data
- **Email Integration**: Notifications, routing, and document distribution
- **Fast Retrieval System**: Indexed search with embeddings for semantic matching
- **LLM Analysis**: Optional deeper analysis via Gemini 2.5 Flash

## Project Layout
```
kmrl_docsense_ai/
  app.py                 # Main Gradio application
  requirements.txt       # Python dependencies
  .env.example          # Environment configuration template
  README.md             # This documentation
  src/
    document_processor.py    # Document processing & multilingual support
    gemini_analyzer.py       # LLM analysis integration
    knowledge_graph.py       # Knowledge graph generation
    compliance_monitor.py    # Compliance rule checking
    storage.py               # Document storage and history
    analyzer_router.py       # LLM router
    email_integration.py     # Email notifications and routing
    advanced_search.py       # Full-text, semantic, and hybrid search
    data_integration.py      # UNS, Maximo, SharePoint simulations
  data/
    docsense.db            # SQLite database for document storage
    sample_docs/           # Sample documents for testing
  assets/
    logos/                 # KMRL branding assets
```
    gemini_analyzer.py
    knowledge_graph.py
    compliance_monitor.py
  data/
    sample_docs/
  assets/
    logos/
```

## Setup (Windows PowerShell)

1) **Create and activate virtual environment**
```powershell
python -m venv "d:\SIH PS@\kmrl_docsense_ai\.venv"
& "d:\SIH PS@\kmrl_docsense_ai\.venv\Scripts\Activate.ps1"
```

2) **Install dependencies**
```powershell
pip install -r "d:\SIH PS@\kmrl_docsense_ai\requirements.txt"
```

3) **Configure environment variables**
- Copy .env.example to .env
```powershell
notepad "d:\SIH PS@\kmrl_docsense_ai\.env"
```

Add the following (all optional, but enable features):
```
# Optional: Gemini API for deeper LLM analysis
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Fake Gmail integration for notifications
# To set up Gmail:
# 1. Create a Gmail account (e.g., kmrltest@gmail.com)
# 2. Enable 2-factor authentication in Gmail settings
# 3. Generate an App Password: https://support.google.com/accounts/answer/185833
# 4. Use the App Password (not your regular password) below
GMAIL_SMTP_SERVER=smtp.gmail.com
GMAIL_SMTP_PORT=587
GMAIL_USERNAME=yourfake@gmail.com
GMAIL_PASSWORD=your_app_password_here
```

### Gmail Setup Instructions

**For Fake Gmail Integration:**

1. **Create a Gmail Account**: Create a new Gmail account specifically for testing (e.g., `kmrltest@gmail.com`)

2. **Enable 2-Factor Authentication**:
   - Go to Google Account settings
   - Security → 2-Step Verification → Enable

3. **Generate App Password**:
   - In 2-Step Verification settings, scroll down to "App passwords"
   - Select "Mail" and "Other (custom name)"
   - Enter "KMRL Knowledge Engine" as the name
   - Copy the generated 16-character password

4. **Configure .env file**:
   - Use the Gmail address as `GMAIL_USERNAME`
   - Use the App Password as `GMAIL_PASSWORD`
   - Keep the SMTP server and port as shown

**Note**: The app will work without Gmail setup, but email features will be disabled.

4) **Run the KMRL Knowledge Engine**

**Option A: Easy Launch (Windows)**
```cmd
# Double-click start_app.bat or run in command prompt:
start_app.bat
```

**Option B: Manual Launch**
```powershell
python "d:\SIH PS@\kmrl_docsense_ai\app.py"
```

**Option C: If port is busy**
```powershell
# First check and fix port issues:
python "d:\SIH PS@\kmrl_docsense_ai\fix_port.py"

# Then run the app:
python "d:\SIH PS@\kmrl_docsense_ai\app.py"
```

Open the Gradio interface at the URL shown in console (typically http://127.0.0.1:7860 or http://127.0.0.1:8501).

## Usage Guide

### Document Processing
- Upload documents (PDF, DOCX, images)
- System automatically detects language (English/Malayalam/Bilingual)
- Extracts actionable information and compliance flags
- Builds knowledge graph of entities and relationships

### Advanced Search
- **Full-text**: Traditional keyword search
- **Semantic**: AI-powered meaning-based search
- **Hybrid**: Combines both approaches
- Apply metadata filters for precise results

### Real-Time Data Integration
- View live sensor data from UNS simulation
- Monitor asset status and work orders
- Link documents to maintenance activities

### Email Integration
- Send automated notifications when documents are processed
- Route critical information to relevant stakeholders
- Configure recipients for different document types

## Configuration Notes
- Without API keys, the system works with heuristics only
- Email features require Gmail app password (not regular password)
- Real-time data simulation runs automatically in background
- Search indexing happens when documents are saved to history

## Implementation Status

### ✅ Fully Implemented Features
- **Four-Pillar Architecture**: All pillars from the strategic blueprint implemented
- **Document Processing**: OCR, NLP, ML for classification and entity recognition
- **Multilingual Support**: English/Malayalam bilingual detection and processing
- **Advanced Search**: Full-text, semantic, and hybrid search with indexing
- **Real-Time Data Integration**: UNS simulation with live sensor data
- **Email Integration**: SMTP-based notifications and document routing
- **Knowledge Graph**: Interactive visualization of document relationships
- **Compliance Monitoring**: Automatic flagging for regulatory requirements
- **UI/UX**: Complete Gradio interface with all tabs and features
- **Fast Retrieval System**: Indexed search with sentence transformers

### 🔧 Technical Stack
- **Frontend**: Gradio web interface
- **Backend**: Python with modular architecture
- **Search**: Whoosh (full-text) + Sentence Transformers (semantic)
- **Data Storage**: SQLite with document history
- **Email**: SMTP with Gmail integration
- **AI/ML**: Google Gemini 2.5 Flash (optional), scikit-learn, NLTK
- **OCR**: Tesseract (for future image processing)

## Notes
- Works without an API key using heuristics; LLM analysis is added if key is present.
- For images, OCR-free approach limits text extraction; PDFs/DOCX provide better results.
- Extend rules in `src/compliance_monitor.py` and document classification in `src/document_processor.py` as needed.
- Email integration uses Gmail app passwords for security (not regular passwords).
- Real-time data simulation runs automatically and can be extended to real APIs.