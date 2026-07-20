"""Адаптер active-overlay Template Studio к каталогу и сайту."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .storage import PROJECT_ROOT, TemplateStudioStore


def catalogue_module_ids() -> set[str]:
    """Читает известные ID из основного JSON-каталога без его изменения."""
    path = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "catalog.json"
    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    return {item["id"] for item in payload.get("problem_sets", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}


def active_templates(store: TemplateStudioStore | None = None) -> list[dict[str, Any]]:
    return (store or TemplateStudioStore()).load_active_templates()


def active_template_metadata(store: TemplateStudioStore | None = None) -> list[dict[str, Any]]:
    return [
        {
            "template_id": item["template_id"],
            "module_id": item["module_id"],
            "title": f"Template Studio: {item['template_id']}",
            "answer_type": item["answer_type"],
            "answer_status": "verified",
            "source_problem_numbers": [item.get("source_metadata", {}).get("problem_number")],
            "studio_draft_id": item.get("studio_draft_id"),
        }
        for item in active_templates(store)
    ]
