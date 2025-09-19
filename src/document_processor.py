import io
import os
import hashlib
from typing import Dict, Any, Tuple

from langdetect import detect
from PIL import Image
try:
    import pytesseract
except Exception:
    pytesseract = None
from pypdf import PdfReader
from docx import Document as DocxDocument

SUPPORTED_TYPES = (".pdf", ".docx", ".jpg", ".jpeg", ".png")


class DocumentProcessor:
    """Lightweight processor with optional OCR for images.
    - PDF/DOCX: text extraction
    - Images: OCR if pytesseract is available
    """

    def _extract_text_pdf(self, content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            texts = []
            for page in reader.pages[:5]:  # limit for speed
                t = page.extract_text() or ""
                texts.append(t)
            return "\n".join(texts)
        except Exception:
            return ""

    def _extract_text_docx(self, content: bytes) -> str:
        try:
            doc = DocxDocument(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""

    def _extract_text_image(self, content: bytes) -> str:
        try:
            img = Image.open(io.BytesIO(content)).convert("RGB")
        except Exception:
            return ""
        if not pytesseract:
            return ""
        try:
            # OCR; if language packs not installed, defaults to eng
            return pytesseract.image_to_string(img)
        except Exception:
            return ""

    def extract_fulltext(self, content: bytes, ext: str) -> str:
        ext = ext.lower()
        if ext == ".pdf":
            return self._extract_text_pdf(content)
        if ext == ".docx":
            return self._extract_text_docx(content)
        if ext in (".jpg", ".jpeg", ".png"):
            return self._extract_text_image(content)
        if ext == ".txt":
            # Handle plain text files
            try:
                return content.decode('utf-8', errors='ignore')
            except:
                return ""
        return ""

    def file_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def extract_metadata(self, filename: str, content: bytes) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1].lower()
        text = self.extract_fulltext(content, ext)

        # Enhanced language detection for bilingual documents
        lang, is_bilingual = self._detect_language(text)

        # Heuristic document type classification
        doc_type = self._classify(text)

        # Suggest role
        role = "manager"
        if doc_type in ("Safety", "Regulatory"):
            role = "safety_officer"
        elif doc_type in ("Engineering", "Maintenance"):
            role = "engineer"
        elif doc_type in ("Procurement", "Finance"):
            role = "finance_officer"

        return {
            "ext": ext,
            "language": lang,
            "is_bilingual": is_bilingual,
            "doc_type": doc_type,
            "suggested_role": role,
            "char_count": len(text),
        }

    def _detect_language(self, text: str) -> Tuple[str, bool]:
        """Enhanced language detection for bilingual English-Malayalam documents"""
        if not text or len(text.strip()) < 10:
            return "unknown", False

        sample = text.strip().replace("\n", " ")[:2000]  # Increased sample size

        # Try to detect on the whole sample first
        try:
            primary_lang = detect(sample)
            # Simple heuristic for Malayalam content
            if 'malayalam' in sample.lower() or 'സുരക്ഷാ' in sample or 'യാത്രക്കാർക്ക്' in sample:
                if primary_lang == 'en':
                    return "bilingual_en_ml", True
                else:
                    return "malayalam", False
            return primary_lang, False
        except:
            # Fallback to sentence-by-sentence detection
            import re
            sentences = re.split(r'[.!?]\s*', sample)
            languages = []

            for sentence in sentences[:5]:  # Check first 5 sentences
                if sentence.strip() and len(sentence) > 20:
                    try:
                        lang = detect(sentence)
                        languages.append(lang)
                    except:
                        continue

            if not languages:
                return "unknown", False

            # Check for bilingual
            has_english = 'en' in languages
            has_malayalam = 'ml' in languages or any('malayalam' in lang.lower() for lang in languages)

            if has_english and has_malayalam:
                return "bilingual_en_ml", True
            elif has_malayalam:
                return "malayalam", False
            elif has_english:
                return "english", False
            else:
                return languages[0], False

    def _classify(self, text: str) -> str:
        if not text:
            return "Unknown"
        t = text.lower()

        # More flexible keyword matching
        if any(k in t for k in ["purchase", "order", "invoice", "tender", "vendor", "procurement"]):
            return "Procurement"
        if any(k in t for k in ["maintenance", "work order", "job card", "asset", "repair", "inspection"]):
            return "Maintenance"
        if any(k in t for k in ["safety", "incident", "near miss", "cmrs", "bulletin", "emergency", "evacuation"]):
            return "Safety"
        if any(k in t for k in ["drawing", "specification", "design", "engineering", "technical"]):
            return "Engineering"
        if any(k in t for k in ["policy", "hr", "human resource", "leave", "recruitment", "staff"]):
            return "HR"
        if any(k in t for k in ["directive", "regulation", "ministry", "compliance", "regulatory"]):
            return "Regulatory"
        if any(k in t for k in ["announcement", "passenger", "train", "station", "platform"]):
            return "Operations"
        return "General"

    def quick_skim(self, content: bytes, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Produce actionable snippets without LLM: bullets, dates, amounts, risks (heuristics)."""
        text = self.extract_fulltext(content, meta.get("ext", ""))

        # Extract simple cues
        bullets = []
        for line in (text or "").splitlines():
            ls = line.strip()
            if not ls:
                continue
            if ls[0] in "-•*" or ls[:2] in ("->", "=>"):
                bullets.append(ls[:200])
        bullets = bullets[:10]

        # Naive date/amount find
        import re
        dates = re.findall(r"\b(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text or "")[:10]
        amounts = re.findall(r"\b₹?\s?\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", text or "")[:10]

        # Risks: look for key risk words
        risks = [l.strip()[:200] for l in (text or "").splitlines() if any(k in l.lower() for k in ["risk", "hazard", "non-conform", "delay", "penalty"])]
        risks = risks[:5]

        return {
            "bullets": bullets,
            "dates": dates,
            "amounts": amounts,
            "risks": risks,
        }