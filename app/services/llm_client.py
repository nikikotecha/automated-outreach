from __future__ import annotations

import json
from typing import Any
from openai import AzureOpenAI

from app.config import settings


class LLMClient:
    def __init__(self) -> None:
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            self.client = None
        else:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )

    def is_configured(self) -> bool:
        return self.client is not None and bool(settings.azure_openai_deployment)

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.is_configured():
            return {}
        response = self.client.chat.completions.create(
            model=settings.azure_openai_deployment,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self.is_configured():
            return ""
        response = self.client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
