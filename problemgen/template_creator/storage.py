"""Изолированное атомарное хранилище provider-generated JSON drafts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from problemgen.template_studio.storage import PROJECT_ROOT, TemplateStudioStore


class TemplateCreatorStore(TemplateStudioStore):
    """Тот же атомарный JSON-механизм, но в отдельном namespace Creator."""

    def __init__(self, root: Path | None = None) -> None:
        selected = root or PROJECT_ROOT / "data" / "template_creator"
        super().__init__(selected)

    def save_creator_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        return self.save_draft(draft)
