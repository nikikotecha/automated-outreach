from __future__ import annotations

import re
from dataclasses import dataclass
from app.services.llm_client import LLMClient


@dataclass
class ExtractedLead:
    full_name: str | None
    role: str | None
    company: str | None
    domain: str | None


class EntityExtractor:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def extract(self, text: str, source_url: str | None = None) -> list[ExtractedLead]:
        if self.llm.is_configured():
            system_prompt = (
                "Extract prospect details from public text. "
                "Return JSON with 'leads' array of objects {full_name, role, company, domain}."
            )
            user_prompt = f"Text: {text}\nSource: {source_url or ''}"
            data = self.llm.chat_json(system_prompt, user_prompt)
            leads = data.get("leads", []) if isinstance(data, dict) else []
            extracted: list[ExtractedLead] = []
            for lead in leads:
                if not isinstance(lead, dict):
                    continue
                extracted.append(
                    ExtractedLead(
                        full_name=lead.get("full_name"),
                        role=lead.get("role"),
                        company=lead.get("company"),
                        domain=lead.get("domain"),
                    )
                )
            return extracted

        name_match = re.search(r"([A-Z][a-z]+\s[A-Z][a-z]+)", text)
        company_match = re.search(r"at\s([A-Z][A-Za-z0-9&\-\s]+)", text)
        return [
            ExtractedLead(
                full_name=name_match.group(1) if name_match else None,
                role=None,
                company=company_match.group(1).strip() if company_match else None,
                domain=None,
            )
        ]
