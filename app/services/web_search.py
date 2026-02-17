from __future__ import annotations

import re
from dataclasses import dataclass
from serpapi import GoogleSearch

from app.config import settings


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class WebSearch:
    def __init__(self) -> None:
        self.api_key = settings.serpapi_key

    def search(self, query: str, limit: int | None = None) -> list[SearchResult]:
        limit = limit or settings.web_results_per_query
        if not self.api_key:
            print("SerpAPI key not configured")
            return []
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": limit,
            }
            search = GoogleSearch(params)
            results_dict = search.get_dict()
            results: list[SearchResult] = []
            
            for item in results_dict.get("organic_results", []):
                url = item.get("link")
                title = item.get("title")
                snippet = item.get("snippet")
                
                if url and title:
                    results.append(SearchResult(title=title, url=url, snippet=snippet or ""))
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            print(f"SerpAPI error: {e}")
            return []


def extract_domains(results: list[SearchResult]) -> list[str]:
    domains: list[str] = []
    for result in results:
        match = re.search(r"https?://([^/]+)/?", result.url)
        if match:
            domains.append(match.group(1).lower())
    return domains


def extract_linkedin_profiles(results: list[SearchResult]) -> list[dict]:
    """Extract LinkedIn profile information from search results"""
    profiles = []
    for result in results:
        if "linkedin.com" in result.url.lower():
            # Parse name from URL: https://uk.linkedin.com/in/john-smith-123456
            match = re.search(r"/in/([a-z0-9-]+)", result.url)
            if match:
                username = match.group(1)
                # Convert URL slug to readable name
                name = username.replace("-", " ").title()
                # Remove trailing numbers
                name = re.sub(r'\s*\d+\s*$', '', name)
                profiles.append({
                    "name": name,
                    "linkedin_url": result.url,
                    "title_snippet": result.title,
                    "description": result.snippet
                })
    return profiles
