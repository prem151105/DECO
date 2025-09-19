from typing import Dict, Any, Optional

from .gemini_analyzer import GeminiAnalyzer, GeminiUnavailable


class AnalyzerRouter:
    """Route to available analyzer backend based on configuration and availability.
    Currently supports: Gemini; easily extensible to add Llama/Ollama/etc.
    """

    def __init__(self, provider: str):
        self.provider = provider
        self.gemini: Optional[GeminiAnalyzer] = None
        if provider == "gemini":
            try:
                self.gemini = GeminiAnalyzer()
            except GeminiUnavailable:
                self.gemini = None

    @property
    def ready(self) -> bool:
        if self.provider == "gemini":
            return self.gemini is not None
        return False

    def analyze(self, content: bytes, role: str = "manager") -> Dict[str, Any]:
        if self.provider == "gemini" and self.gemini:
            try:
                return self.gemini.analyze_document(content, role=role)
            except Exception as e:
                return {"error": str(e)}
        # default no-LLM path
        return {}