from __future__ import annotations

from app.services.llm_client import LLMClient


class QueryGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate_queries(self, icp_prompt: str, limit: int = 6) -> list[str]:
        if not self.llm.is_configured():
            return [icp_prompt]
        system_prompt = (
            "You generate concise web search queries to find public prospects. "
            "Return JSON with a 'queries' array of strings. "
            "Include both LinkedIn searches and company website searches."
        )
        user_prompt = (
            f"ICP: {icp_prompt}\n"
            f"Generate {limit} queries. Mix LinkedIn profile searches with company website searches. "
            f"Example LinkedIn query: 'site:linkedin.com/in {icp_prompt}'\n"
            f"Example company query: '{icp_prompt} company UK'"
        )
        data = self.llm.chat_json(system_prompt, user_prompt)
        queries = data.get("queries", []) if isinstance(data, dict) else []
        
        # Keep all queries including LinkedIn
        filtered = []
        for q in queries:
            if q and isinstance(q, str):
                filtered.append(q.strip())
        
        return filtered[:limit]
