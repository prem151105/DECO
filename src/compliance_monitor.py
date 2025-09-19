from typing import Dict, Any, List

# Simple rules to mimic CMRS/MoHUA compliance checks. Extend as needed.
RULES = [
    {
        "id": "cmrs-directive",
        "keywords": ["cmrs", "commissioner of metro rail safety", "directive", "circular"],
        "message": "Potential regulatory directive detected. Ensure actions logged and acknowledged within 48 hours.",
        "severity": "high",
    },
    {
        "id": "incident-report",
        "keywords": ["incident", "accident", "near miss", "safety"],
        "message": "Incident-related content. Verify entry in safety log and corrective actions.",
        "severity": "high",
    },
    {
        "id": "procurement",
        "keywords": ["purchase order", "invoice", "tender", "bid", "vendor"],
        "message": "Procurement document. Check approvals and budget alignment.",
        "severity": "medium",
    },
    {
        "id": "maintenance",
        "keywords": ["maintenance", "work order", "job card", "asset"],
        "message": "Maintenance content. Ensure job closure and MTBF tracking.",
        "severity": "medium",
    }
]


class ComplianceMonitor:
    def check(self, meta: Dict[str, Any], quick: Dict[str, Any], llm: Dict[str, Any] | None) -> List[Dict[str, str]]:
        hits = []
        text_parts: List[str] = []
        text_parts.extend(quick.get("bullets", []))
        text_parts.extend(quick.get("risks", []))
        if llm and isinstance(llm, dict):
            text_parts.extend([str(x) for x in llm.get("risks", [])])
            text_parts.extend([str(x) for x in llm.get("summary", [])])

        blob = "\n".join(text_parts).lower()
        for rule in RULES:
            if any(k in blob for k in rule["keywords"]):
                hits.append({"id": rule["id"], "message": rule["message"], "severity": rule["severity"]})
        return hits