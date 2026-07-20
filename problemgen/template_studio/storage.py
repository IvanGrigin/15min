"""Файловое, атомарное и изолированное хранилище Template Studio."""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORAGE_ROOT = PROJECT_ROOT / "data" / "template_studio"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class TemplateStudioStore:
    """Хранит drafts отдельно и публикует только активный overlay-каталог."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_STORAGE_ROOT
        self.drafts_root = self.root / "drafts"
        self.history_root = self.root / "history"
        self.reports_root = self.root / "validation_reports"
        self.active_catalogue_path = self.root / "active_templates.json"
        for directory in (self.drafts_root, self.history_root, self.reports_root):
            directory.mkdir(parents=True, exist_ok=True)
        if not self.active_catalogue_path.exists():
            self._atomic_write(self.active_catalogue_path, {"schema_version": 1, "templates": []})

    def load_draft(self, draft_id: str) -> dict[str, Any]:
        path = self.drafts_root / f"{draft_id}.json"
        if not path.is_file():
            raise KeyError("Черновик не найден.")
        return self._read_json(path)

    def list_drafts(self) -> list[dict[str, Any]]:
        drafts = [self._read_json(path) for path in self.drafts_root.glob("*.json")]
        return sorted(drafts, key=lambda draft: draft.get("updated_at", ""), reverse=True)

    def save_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        saved = deepcopy(draft)
        self._atomic_write(self.drafts_root / f"{saved['draft_id']}.json", saved)
        return saved

    def delete_draft_file(self, draft_id: str) -> None:
        path = self.drafts_root / f"{draft_id}.json"
        if path.exists():
            path.unlink()

    def load_active_templates(self) -> list[dict[str, Any]]:
        catalogue = self._read_json(self.active_catalogue_path)
        templates = catalogue.get("templates", [])
        if not isinstance(templates, list):
            raise ValueError("Каталог активных шаблонов Template Studio повреждён.")
        return templates

    def active_templates_for_module(self, module_id: str) -> list[dict[str, Any]]:
        return [template for template in self.load_active_templates() if template.get("module_id") == module_id]

    def activate(self, template: dict[str, Any]) -> None:
        catalogue = self._read_json(self.active_catalogue_path)
        templates = list(catalogue.get("templates", []))
        template_id = template["template_id"]
        if any(existing.get("template_id") == template_id for existing in templates):
            raise ValueError(f"В active-каталоге уже есть template_id {template_id}.")
        backup = self.history_root / f"catalogue_before_{utc_now().replace(':', '-')}.json"
        self._atomic_write(backup, catalogue)
        templates.append(deepcopy(template))
        self._atomic_write(self.active_catalogue_path, {"schema_version": 1, "templates": templates})

    def archive_active(self, template_id: str) -> None:
        catalogue = self._read_json(self.active_catalogue_path)
        templates = list(catalogue.get("templates", []))
        retained = [template for template in templates if template.get("template_id") != template_id]
        if len(retained) == len(templates):
            raise KeyError("Активный шаблон не найден в overlay-каталоге.")
        backup = self.history_root / f"catalogue_before_{utc_now().replace(':', '-')}.json"
        self._atomic_write(backup, catalogue)
        self._atomic_write(self.active_catalogue_path, {"schema_version": 1, "templates": retained})

    def save_report(self, draft_id: str, report: dict[str, Any]) -> None:
        self._atomic_write(self.reports_root / f"{draft_id}.json", report)

    def append_history(self, draft_id: str, event: dict[str, Any]) -> None:
        path = self.history_root / f"{draft_id}.json"
        history = self._read_json(path) if path.exists() else {"draft_id": draft_id, "events": []}
        history.setdefault("events", []).append(deepcopy(event))
        self._atomic_write(path, history)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as source:
            payload = json.load(source)
        if not isinstance(payload, dict):
            raise ValueError(f"Ожидался JSON-объект: {path.name}")
        return payload

    @staticmethod
    def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as target:
                json.dump(payload, target, ensure_ascii=False, indent=2)
                target.write("\n")
            os.replace(temporary_name, path)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
