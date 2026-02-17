from __future__ import annotations

from app.config import settings
from app.services.llm_client import LLMClient


class EmailPersonalizer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def draft(self, lead_name: str | None, lead_role: str | None, company: str | None, context: str) -> tuple[str, str]:
        sender_profile = (
            f"Sender: {settings.sender_name}, {settings.sender_title} at {settings.sender_company}. "
            f"Value: {settings.sender_value_prop}"
        )
        if not self.llm.is_configured():
            subject = f"Quick idea for {company or 'your team'}"
            body = (
                f"Hi {lead_name or 'there'},\n\n"
                f"Noticed your work at {company or 'your company'}. "
                f"{settings.sender_value_prop} "
                "If it helps, happy to share a quick walkthrough.\n\n"
                f"Best,\n{settings.sender_name}"
            )
            return subject, body
        try:
            system_prompt = (
                "Write a concise, personalized outreach email. "
                "Return JSON {subject:string, body:string}. Keep it under 120 words."
            )
            user_prompt = (
                f"{sender_profile}\n"
                f"Lead: {lead_name}, Role: {lead_role}, Company: {company}\n"
                f"Context: {context}"
            )
            data = self.llm.chat_json(system_prompt, user_prompt)
            subject = data.get("subject", "Quick question") if isinstance(data, dict) else "Quick question"
            body = data.get("body", "") if isinstance(data, dict) else ""
            return subject, body
        except Exception:
            subject = f"Quick idea for {company or 'your team'}"
            body = (
                f"Hi {lead_name or 'there'},\n\n"
                f"Noticed your work at {company or 'your company'}. "
                f"{settings.sender_value_prop} "
                "If it helps, happy to share a quick walkthrough.\n\n"
                f"Best,\n{settings.sender_name}"
            )
            return subject, body
