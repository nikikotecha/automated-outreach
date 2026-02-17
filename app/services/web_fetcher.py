from __future__ import annotations

import re
import httpx
from bs4 import BeautifulSoup
import time

from app.services.web_search import USER_AGENT

# Sites that commonly block bots
BLOCKED_DOMAINS = {
    "indeed.com",
    "linkedin.com",
    "glassdoor.com",
    "monster.com",
    "totaljobs.com",
    "jobs.ac.uk",
}


class WebFetcher:
    def __init__(self) -> None:
        self.client = httpx.Client(timeout=20.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True)

    def _is_blocked_domain(self, url: str) -> bool:
        """Check if URL is from a domain that's likely to block bots"""
        for blocked in BLOCKED_DOMAINS:
            if blocked in url.lower():
                return True
        return False

    def fetch_text(self, url: str) -> str:
        # Skip fetching from known blocked domains
        if self._is_blocked_domain(url):
            return ""
        
        try:
            response = self.client.get(url)
            # 403, 401, 429 are common bot-detection responses
            if response.status_code in [403, 401, 429]:
                return ""
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = " ".join(soup.stripped_strings)
            text = re.sub(r"\s+", " ", text)
            return text[:4000]
        except Exception:
            # Return empty string on any error instead of raising
            return ""
