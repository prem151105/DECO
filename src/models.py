from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Metadata:
    ext: str
    language: str
    doc_type: str
    suggested_role: str
    char_count: int


@dataclass
class QuickView:
    bullets: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    amounts: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class LLMAnalysis:
    classification: Optional[str] = None
    key_entities: List[str] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    compliance: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    summary: List[str] = field(default_factory=list)
    raw: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ComplianceFlag:
    id: str
    message: str
    severity: str


@dataclass
class DocRecord:
    filename: str
    file_hash: str
    metadata: Metadata
    quick_view: QuickView
    llm_analysis: Optional[LLMAnalysis]
    compliance: List[ComplianceFlag]
    doc_id: Optional[int] = None