from __future__ import annotations

import uuid
import logging
from datetime import datetime

from app.config import settings

# Setup logging to file for background tasks
logging.basicConfig(
    filename='/tmp/outreach_pipeline.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from app.services.entity_extractor import EntityExtractor
from app.services.email_guesser import guess_emails
from app.services.email_personalizer import EmailPersonalizer
from app.services.query_generator import QueryGenerator
from app.services.relevance_scorer import RelevanceScorer
from app.services.web_fetcher import WebFetcher
from app.services.web_search import WebSearch, extract_linkedin_profiles
from app.storage.table_storage import TableStore
from app.utils.text import summarize_context


class CampaignPipeline:
    def __init__(self, store: TableStore, query_generator: QueryGenerator, extractor: EntityExtractor) -> None:
        self.store = store
        self.query_generator = query_generator
        self.extractor = extractor
        self.web_search = WebSearch()
        self.web_fetcher = WebFetcher()
        self.relevance = RelevanceScorer(query_generator.llm)
        self.personalizer = EmailPersonalizer(query_generator.llm)

    def run_campaign(self, campaign_id: str) -> int:
        campaign = self.store.get_campaign(campaign_id)
        if not campaign:
            return 0
        icp_prompt = campaign.get("icp_prompt", "")
        max_leads = int(campaign.get("max_leads", settings.max_pages_to_fetch))
        logger.info(f"=== Starting campaign {campaign_id} ===")
        logger.info(f"ICP: {icp_prompt}")
        logger.info(f"Max leads: {max_leads}")
        logger.info(f"SerpAPI key: {settings.serpapi_key[:20] if settings.serpapi_key else 'NOT SET'}...")
        
        try:
            queries = self.query_generator.generate_queries(icp_prompt)
            logger.info(f"Generated {len(queries)} queries: {queries}")
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            queries = [icp_prompt]
        total_queries = len(queries)
        queries_completed = 0
        self.store.update_campaign(
            campaign_id,
            status="RUNNING",
            query_count=total_queries,
            total_queries=total_queries,
            queries_completed=queries_completed,
            leads_created=0,
            last_step="queries_generated",
        )

        leads_created = 0
        linkedin_profiles = []
        for query in queries:
            logger.info(f"Searching for: {query}")
            try:
                results = self.web_search.search(query)
                logger.info(f"  Found {len(results)} results")
                
                # Extract LinkedIn profiles from this query's results
                if "linkedin" in query.lower():
                    linkedin_profiles.extend(extract_linkedin_profiles(results))
                    logger.info(f"  Found {len(extract_linkedin_profiles(results))} LinkedIn profiles")
            except Exception as e:
                logger.error(f"  Error searching: {e}")
                continue
            for result in results:
                if leads_created >= max_leads:
                    break
                logger.info(f"  Processing: {result.url}")
                try:
                    page_text = self.web_fetcher.fetch_text(result.url)
                    if not page_text:
                        logger.debug(f"    Skipped (empty/blocked content)")
                        continue
                    logger.debug(f"    Fetched text ({len(page_text)} chars)")
                except Exception as e:
                    logger.error(f"    Fetch error: {e}")
                    continue
                lead_context = f"{result.title}. {result.snippet}. {page_text}"
                try:
                    extracted = self.extractor.extract(lead_context, result.url)
                    logger.info(f"    Extracted {len(extracted)} leads")
                except Exception as e:
                    logger.error(f"    Extract error: {e}")
                    extracted = []
                if not extracted:
                    logger.debug(f"    No leads extracted")
                    continue
                for lead in extracted:
                    if leads_created >= max_leads:
                        break
                    lead_id = str(uuid.uuid4())
                    email_candidates = guess_emails(lead.full_name, lead.domain)
                    try:
                        score, reason = self.relevance.score(icp_prompt, lead_context)
                    except Exception as e:
                        logger.error(f"Error scoring relevance: {e}")
                        score, reason = 50, "Error during scoring"
                    try:
                        subject, body = self.personalizer.draft(
                            lead.full_name, lead.role, lead.company, result.snippet
                        )
                    except Exception as e:
                        logger.error(f"Error personalizing email: {e}")
                        subject, body = f"Hello {lead.full_name or 'there'}", ""
                    payload = {
                        "full_name": lead.full_name,
                        "role": lead.role,
                        "company": lead.company,
                        "domain": lead.domain,
                        "source_url": result.url,
                        "score": score,
                        "score_reason": reason,
                        "email_candidates": ",".join(email_candidates),  # Convert to string
                        "selected_email": email_candidates[0] if email_candidates else None,
                        "outreach_subject": subject,
                        "outreach_body": body,
                        "status": "DRAFTED",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                    self.store.upsert_lead(campaign_id, lead_id, payload)
                    leads_created += 1
                    self.store.update_campaign(
                        campaign_id,
                        leads_created=leads_created,
                        last_step="lead_created",
                    )
                    logger.info(f"  Created lead: {lead.full_name}")
            if leads_created >= max_leads:
                break
            queries_completed += 1
            self.store.update_campaign(
                campaign_id,
                queries_completed=queries_completed,
                leads_created=leads_created,
                last_step="query_complete",
            )
        
        # Store LinkedIn profiles found during search as leads too
        for profile in linkedin_profiles:
            if leads_created >= max_leads:
                break
            lead_id = str(uuid.uuid4())
            # LinkedIn profiles don't have email, but we have the URL
            payload = {
                "full_name": profile.get("name"),
                "role": profile.get("title_snippet", ""),
                "company": "",
                "domain": "linkedin.com",
                "source_url": profile.get("linkedin_url"),
                "score": 0,
                "score_reason": "LinkedIn profile found during search",
                "email_candidates": "",
                "selected_email": None,
                "outreach_subject": f"Found you on LinkedIn",
                "outreach_body": f"LinkedIn Profile: {profile.get('linkedin_url')}\n\n{profile.get('description', '')}",
                "status": "LINKEDIN_PROFILE",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            try:
                self.store.upsert_lead(campaign_id, lead_id, payload)
                leads_created += 1
                self.store.update_campaign(
                    campaign_id,
                    leads_created=leads_created,
                    last_step="linkedin_profile_stored",
                )
                logger.info(f"  Stored LinkedIn profile: {profile.get('name')}")
            except Exception as e:
                logger.error(f"  Error storing LinkedIn profile: {e}")
        
        self.store.update_campaign(
            campaign_id,
            status="READY",
            queries_completed=queries_completed,
            leads_created=leads_created,
            last_step="complete",
        )
        logger.info(f"=== Campaign {campaign_id} finished with {leads_created} leads ===" )
        return leads_created

    def generate_followups(self, campaign_id: str) -> int:
        leads = self.store.list_leads(campaign_id)
        updated = 0
        for lead in leads:
            if lead.get("status") != "SENT":
                continue
            context = summarize_context(lead)
            subject, body = self.personalizer.draft(
                lead.get("full_name"), lead.get("role"), lead.get("company"), context
            )
            self.store.upsert_lead(
                campaign_id,
                lead["RowKey"],
                {
                    "outreach_subject": subject,
                    "outreach_body": body,
                    "status": "FOLLOWUP_DRAFTED",
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            updated += 1
        return updated
