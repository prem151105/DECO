import os
from typing import Optional


class Settings:
    """Centralized app settings loaded from environment (.env supported)."""

    def __init__(self) -> None:
        self.google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
        # Where to place SQLite DB; defaults to data/docsense.db under project
        self.storage_path: str = os.getenv("DS_STORAGE_PATH", "data/docsense.db")
        # Max PDF pages to read during quick skim
        self.max_pdf_pages: int = int(os.getenv("DS_MAX_PDF_PAGES", "5"))
        # Default analyzer provider: none|gemini
        self.default_analyzer: str = os.getenv("DS_ANALYZER", "gemini" if self.google_api_key else "none")
        # LLM request timeout (seconds)
        self.llm_timeout: int = int(os.getenv("DS_LLM_TIMEOUT", "45"))


settings = Settings()