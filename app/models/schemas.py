from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.utcnow()


class CampaignCreate(BaseModel):
    icp_prompt: str
    max_leads: int = 25


class Campaign(BaseModel):
    id: str
    icp_prompt: str
    max_leads: int
    created_at: datetime = Field(default_factory=utc_now)
    status: str = "NEW"
    query_count: int = 0


class Lead(BaseModel):
    id: str
    campaign_id: str
    full_name: str | None = None
    role: str | None = None
    company: str | None = None
    domain: str | None = None
    source_url: str | None = None
    score: int | None = None
    score_reason: str | None = None
    email_candidates: list[str] = []
    selected_email: str | None = None
    outreach_subject: str | None = None
    outreach_body: str | None = None
    status: str = "NEW"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_sent_at: datetime | None = None


class LeadUpdate(BaseModel):
    selected_email: str | None = None
    outreach_subject: str | None = None
    outreach_body: str | None = None
    status: str | None = None


class OutreachLog(BaseModel):
    id: str
    campaign_id: str
    lead_id: str
    event_type: str
    payload: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=utc_now)
