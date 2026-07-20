"""Сменяемые AI-провайдеры для Template Creator без ключей в репозитории."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol


class ProviderError(RuntimeError):
    """Провайдер недоступен или вернул нестрогое структурированное содержимое."""


class MathTemplateGenerationProvider(Protocol):
    def generate_template(self, problem_text: str, repository_context: dict[str, Any], *, repair_errors: list[str] | None = None) -> dict[str, Any]: ...


class OpenAICompatibleTemplateProvider:
    """HTTP-адаптер OpenAI-compatible chat endpoint с JSON-only контрактом."""

    def __init__(self, endpoint: str, api_key: str, model: str, timeout_seconds: int = 25) -> None:
        self.endpoint, self.api_key, self.model, self.timeout_seconds = endpoint, api_key, model, timeout_seconds

    def generate_template(self, problem_text: str, repository_context: dict[str, Any], *, repair_errors: list[str] | None = None) -> dict[str, Any]:
        instruction = {
            "task": "Return exactly one JSON object for a mathematical parameterized template. No Markdown or prose.",
            "problem": problem_text,
            "repository_context": repository_context,
            "repair_errors": repair_errors or [],
        }
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": json.dumps(instruction, ensure_ascii=False)}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            candidate = json.loads(content) if isinstance(content, str) else content
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ProviderError("Провайдер не вернул корректный JSON-шаблон.") from error
        if not isinstance(candidate, dict):
            raise ProviderError("Провайдер должен вернуть JSON-объект шаблона.")
        return candidate


def provider_from_environment() -> MathTemplateGenerationProvider | None:
    """Создаёт провайдера только при полной явной конфигурации окружения."""
    endpoint = os.getenv("TEMPLATE_CREATOR_PROVIDER_URL", "").strip()
    api_key = os.getenv("TEMPLATE_CREATOR_API_KEY", "").strip()
    model = os.getenv("TEMPLATE_CREATOR_MODEL", "").strip()
    if not endpoint or not api_key or not model:
        return None
    return OpenAICompatibleTemplateProvider(endpoint, api_key, model)
