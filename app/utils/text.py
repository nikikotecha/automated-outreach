from __future__ import annotations

from typing import Any


def summarize_context(lead: dict[str, Any]) -> str:
    parts = [
        lead.get("full_name"),
        lead.get("role"),
        lead.get("company"),
        lead.get("source_url"),
    ]
    return ", ".join([p for p in parts if p])
