from __future__ import annotations

from app.services.llm_client import LLMClient


class RelevanceScorer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def score(self, icp_prompt: str, lead_context: str) -> tuple[int, str]:
        if not self.llm.is_configured():
            score = 50 if icp_prompt.lower() in lead_context.lower() else 30
            return score, "Heuristic match"
        system_prompt = (
            "Score lead relevance to ICP from 0 to 100. "
            "Return JSON {score:int, reason:string}."
        )
        user_prompt = f"ICP: {icp_prompt}\nLead Context: {lead_context}"
        data = self.llm.chat_json(system_prompt, user_prompt)
        score = int(data.get("score", 0)) if isinstance(data, dict) else 0
        reason = data.get("reason", "") if isinstance(data, dict) else ""
        return max(0, min(score, 100)), reason
