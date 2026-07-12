from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "templates" / "problem_templates.json"
_PLACEHOLDER_RE = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")
_REQUIRED_FIELDS = ("template_id", "domain", "module", "topic", "problem_type", "difficulty", "template_text")


class TemplateCatalogError(ValueError):
    """Raised when the static template catalog is malformed."""


def template_placeholders(template_text: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(template_text))


def validate_template(template: dict[str, Any]) -> None:
    missing = [field for field in _REQUIRED_FIELDS if not template.get(field)]
    if missing:
        raise TemplateCatalogError(f"У шаблона нет обязательных полей: {', '.join(missing)}.")

    placeholders = template_placeholders(template["template_text"])
    declared = set(template.get("placeholders", {}).get("characters", []))
    declared.update(template.get("placeholders", {}).get("locations", []))
    declared.update(template.get("placeholders", {}).get("numbers", []))
    declared.update(template.get("derived_words", {}))
    unknown = placeholders - declared
    if unknown:
        raise TemplateCatalogError(
            f"Шаблон {template['template_id']} содержит неописанные плейсхолдеры: {', '.join(sorted(unknown))}."
        )

    number_slots = set(template.get("placeholders", {}).get("numbers", []))
    constraints = template.get("constraints", {})
    missing_constraints = number_slots - set(constraints)
    if missing_constraints:
        raise TemplateCatalogError(
            f"Шаблон {template['template_id']} не задаёт constraints для: {', '.join(sorted(missing_constraints))}."
        )

    for slot, word_rule in template.get("derived_words", {}).items():
        if word_rule.get("number") not in number_slots or len(word_rule.get("forms", [])) != 3:
            raise TemplateCatalogError(f"Некорректное правило словоформы {slot} в {template['template_id']}.")


@lru_cache(maxsize=8)
def _read_and_validate(resolved_path: Path, _mtime_ns: int) -> tuple[dict[str, Any], ...]:
    # Кэш ключуется по (пути, времени изменения файла): пока JSON не менялся,
    # каталог читается и валидируется один раз, а после правки файла _mtime_ns
    # меняется и запись перечитывается автоматически, без перезапуска процесса.
    with resolved_path.open(encoding="utf-8") as source:
        payload = json.load(source)
    templates = payload.get("templates")
    if not isinstance(templates, list) or not templates:
        raise TemplateCatalogError("В каталоге templates должен быть непустой список.")
    ids: set[str] = set()
    for template in templates:
        validate_template(template)
        template_id = template["template_id"]
        if template_id in ids:
            raise TemplateCatalogError(f"Повторяющийся template_id: {template_id}.")
        ids.add(template_id)
    return tuple(templates)


def load_template_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    templates = _read_and_validate(resolved, resolved.stat().st_mtime_ns)
    return list(templates)


def find_templates(module: str, difficulty: int, path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, Any]]:
    if not 1 <= difficulty <= 10:
        raise ValueError("Сложность должна быть в диапазоне от 1 до 10.")
    return [
        template for template in load_template_catalog(path)
        if template["module"] == module and difficulty in template.get("supported_difficulties", [template["difficulty"]])
    ]


def list_modules(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, Any]]:
    modules: dict[str, dict[str, Any]] = {}
    for template in load_template_catalog(path):
        module = template["module"]
        item = modules.setdefault(
            module,
            {"id": module, "title": template["title"], "domain": template["domain"], "available_difficulties": set()},
        )
        item["available_difficulties"].update(template.get("supported_difficulties", [template["difficulty"]]))
    return [
        {**item, "available_difficulties": sorted(item["available_difficulties"])}
        for _, item in sorted(modules.items())
    ]
