# Outreach Bot MVP

Code-first MVP for AI prospecting and outreach on Azure.

## Features
- ICP prompt intake
- LLM-generated search queries
- Public web result collection
- Name, role, company extraction
- Email guessing
- LLM relevance scoring
- Personalized outreach emails
- Lead and campaign storage
- Follow-up drafting workflow
- LinkedIn profile discovery (manual outreach)
- Draft review + edit in UI
- Bulk send + CSV export
- Campaign progress status

## Local Setup
1. Copy .env.example to .env and fill Azure settings.
2. Install dependencies from requirements.txt.
3. Start the API with your preferred ASGI runner.

Example:
- `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

Open UI at:
- http://localhost:8000

### Email Sending (ACS)
Email is sent via Azure Communication Services. It will not send unless ACS is configured.

Required .env settings:
- `ACS_EMAIL_CONNECTION_STRING`
- `ACS_EMAIL_SENDER` (must be a verified sender/domain in ACS)

### LinkedIn Profiles
The system can surface LinkedIn profile URLs for manual outreach. LinkedIn connection graphs are not available via public APIs.

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
- If email is not configured, the UI will show “Email: not configured” and sending will fail.
