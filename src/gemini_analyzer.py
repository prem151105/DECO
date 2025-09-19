import os
from typing import Dict, Any

try:
    import google.generativeai as genai
except Exception:
    genai = None


class GeminiUnavailable(Exception):
    pass


class GeminiAnalyzer:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or not genai:
            raise GeminiUnavailable("Gemini not available: missing key or package")
        genai.configure(api_key=api_key)
        # Use 2.5 Flash as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_document(self, file_content: bytes, role: str = "manager") -> Dict[str, Any]:
        prompt = f"""
        You are an assistant for Kochi Metro Rail Limited (KMRL). Analyze the uploaded document and return a concise, role-specific JSON with fields:
        - classification (Engineering/Safety/Procurement/HR/Regulatory/Finance/General)
        - key_entities (list)
        - action_items (list with {{description, owner?, deadline?}})
        - compliance (list of {{regulation, requirement, due_date?}})
        - risks (list)
        - summary (5-7 bullet points tailored for {role})
        Ensure valid JSON only.
        """
        # Send as bytes
        resp = self.model.generate_content([
            {"text": prompt},
            {"inline_data": {"mime_type": "application/octet-stream", "data": file_content}}
        ])
        text = resp.text or "{}"
        # Best-effort JSON parse
        import json
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}