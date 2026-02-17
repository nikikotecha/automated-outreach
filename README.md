# Outreach Bot MVP

AI‑powered prospecting + outreach MVP on Azure. Discover leads, draft emails, and surface LinkedIn profiles for manual outreach — all from a single workflow.

**Tech:** FastAPI • Azure OpenAI • Azure Table Storage • Azure Communication Services • SerpAPI

## Highlights
- LLM‑generated search queries from ICP prompts
- Lead enrichment (name, role, company, domain)
- Relevance scoring + personalized email drafting
- LinkedIn profile discovery for manual outreach
- Draft review + edit in UI before sending
- Bulk send + CSV export
- Campaign progress tracking

## Quickstart
1. Copy .env.example to .env and fill Azure settings.
2. Install dependencies from requirements.txt.
3. Start the API:
	- python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
4. Open UI at http://localhost:8000

### Email Sending (ACS)
Emails are sent via Azure Communication Services. It will not send unless ACS is configured.

Required .env settings:
- `ACS_EMAIL_CONNECTION_STRING`
- `ACS_EMAIL_SENDER` (must be a verified sender/domain in ACS)

### LinkedIn Profiles
The system surfaces LinkedIn profile URLs for manual outreach. LinkedIn connection graphs are not available via public APIs.

## API Overview
- POST /campaigns
- POST /campaigns/{campaign_id}/run
- GET /campaigns/{campaign_id}
- GET /campaigns/{campaign_id}/leads
- GET /campaigns/{campaign_id}/leads.csv
- PATCH /campaigns/{campaign_id}/leads/{lead_id}
- POST /campaigns/{campaign_id}/leads/send-batch
- GET /campaigns/{campaign_id}/linkedin-profiles
- POST /campaigns/{campaign_id}/leads/{lead_id}/send
- POST /campaigns/{campaign_id}/followups
- GET /status/email

## Notes
- Azure OpenAI is required for LLM-based enrichment.
- Azure Table Storage is used for persistence.
- Azure Communication Services Email is used for sending outreach.
- If email is not configured, the UI shows “Email: not configured” and sending fails.

## Why this project?
This MVP demonstrates end‑to‑end AI prospecting with production‑grade Azure services: search → enrichment → scoring → outreach. It’s designed to be practical, extensible, and recruiter‑friendly.
