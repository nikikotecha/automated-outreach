from __future__ import annotations

from datetime import datetime
import csv
import io
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from app.models.schemas import CampaignCreate, LeadUpdate
from app.config import settings
from app.services.llm_client import LLMClient
from app.services.query_generator import QueryGenerator
from app.services.entity_extractor import EntityExtractor
from app.services.email_sender import EmailSender
from app.storage.table_storage import TableStore
from app.workflows.pipeline import CampaignPipeline


router = APIRouter()
store = TableStore()
llm = LLMClient()
query_generator = QueryGenerator(llm)
extractor = EntityExtractor(llm)
pipeline = CampaignPipeline(store, query_generator, extractor)
email_sender = EmailSender()


@router.post("/campaigns")
def create_campaign(payload: CampaignCreate):
    if not store.service:
        raise HTTPException(status_code=500, detail="Storage is not configured")
    campaign = store.create_campaign(payload.icp_prompt, payload.max_leads)
    return campaign


@router.post("/campaigns/{campaign_id}/run")
def run_campaign(campaign_id: str, background_tasks: BackgroundTasks):
    if not store.service:
        raise HTTPException(status_code=500, detail="Storage is not configured")
    background_tasks.add_task(pipeline.run_campaign, campaign_id)
    return {"status": "queued"}


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    campaign = store.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/status/email")
def email_status():
    return {
        "configured": email_sender.is_configured(),
        "sender": settings.acs_email_sender if email_sender.is_configured() else None,
    }


@router.get("/campaigns/{campaign_id}/leads")
def list_leads(campaign_id: str):
    return store.list_leads(campaign_id)


@router.get("/campaigns/{campaign_id}/leads.csv")
def export_leads_csv(campaign_id: str):
    leads = store.list_leads(campaign_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "full_name",
        "role",
        "company",
        "domain",
        "selected_email",
        "score",
        "status",
        "source_url",
        "outreach_subject",
        "outreach_body",
    ])
    for lead in leads:
        writer.writerow([
            lead.get("full_name", ""),
            lead.get("role", ""),
            lead.get("company", ""),
            lead.get("domain", ""),
            lead.get("selected_email", ""),
            lead.get("score", ""),
            lead.get("status", ""),
            lead.get("source_url", ""),
            lead.get("outreach_subject", ""),
            lead.get("outreach_body", ""),
        ])
    return Response(content=output.getvalue(), media_type="text/csv")


@router.patch("/campaigns/{campaign_id}/leads/{lead_id}")
def update_lead(campaign_id: str, lead_id: str, payload: LeadUpdate):
    lead = store.get_lead(campaign_id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()
    store.upsert_lead(campaign_id, lead_id, update_data)
    return store.get_lead(campaign_id, lead_id)


@router.get("/campaigns/{campaign_id}/linkedin-profiles")
def list_linkedin_profiles(campaign_id: str):
    """Get all LinkedIn profiles found during campaign search"""
    # This is a simple endpoint that returns LinkedIn profiles extracted from source URLs
    leads = store.list_leads(campaign_id)
    linkedin_profiles = []
    
    for lead in leads:
        source_url = lead.get("source_url", "")
        if "linkedin.com" in source_url.lower():
            linkedin_profiles.append({
                "name": lead.get("full_name") or "Unknown",
                "linkedin_url": source_url,
                "company": lead.get("company"),
                "role": lead.get("role"),
                "snippet": lead.get("outreach_subject")
            })
    
    return linkedin_profiles


@router.post("/campaigns/{campaign_id}/leads/{lead_id}/send")
def send_email(campaign_id: str, lead_id: str):
    if not email_sender.is_configured():
        raise HTTPException(status_code=400, detail="Email service not configured")
    lead = store.get_lead(campaign_id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    recipient = lead.get("selected_email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email selected")
    subject = lead.get("outreach_subject") or "Hello"
    body = lead.get("outreach_body") or ""
    message_id = email_sender.send(recipient, subject, body)
    store.upsert_lead(
        campaign_id,
        lead_id,
        {
            "status": "SENT",
            "last_sent_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
    )
    store.add_outreach_log(campaign_id, lead_id, "email_sent", {"message_id": message_id})
    return {"status": "sent", "message_id": message_id}


@router.post("/campaigns/{campaign_id}/leads/send-batch")
def send_batch(campaign_id: str, payload: dict):
    if not email_sender.is_configured():
        raise HTTPException(status_code=400, detail="Email service not configured")
    lead_ids = payload.get("lead_ids", [])
    results = []
    for lead_id in lead_ids:
        lead = store.get_lead(campaign_id, lead_id)
        if not lead:
            results.append({"lead_id": lead_id, "status": "not_found"})
            continue
        recipient = lead.get("selected_email")
        if not recipient:
            results.append({"lead_id": lead_id, "status": "no_email"})
            continue
        subject = lead.get("outreach_subject") or "Hello"
        body = lead.get("outreach_body") or ""
        try:
            message_id = email_sender.send(recipient, subject, body)
            store.upsert_lead(
                campaign_id,
                lead_id,
                {
                    "status": "SENT",
                    "last_sent_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            store.add_outreach_log(campaign_id, lead_id, "email_sent", {"message_id": message_id})
            results.append({"lead_id": lead_id, "status": "sent", "message_id": message_id})
        except Exception as e:
            results.append({"lead_id": lead_id, "status": "error", "error": str(e)})
    return {"results": results}


@router.post("/campaigns/{campaign_id}/followups")
def generate_followups(campaign_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(pipeline.generate_followups, campaign_id)
    return {"status": "queued"}
