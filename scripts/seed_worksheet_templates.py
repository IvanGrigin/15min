"""Публикация шаблонов из библиотеки JSON через полный цикл Template Studio.

Шаблоны лежат в data/template_studio/library/*.json — по одному файлу на задачу.
Python здесь ничего не описывает и не формулирует: он только прогоняет каждый
JSON через draft → update → validate (10 сидов с независимым пересчётом) → activate.

Чтобы добавить новую задачу, положите ещё один JSON в библиотеку. Правила и
пошаговый алгоритм — в docs/AGENT_TASK_TO_TEMPLATE_PROMPT.md.

Запуск:
    python3 scripts/seed_worksheet_templates.py                     # опубликовать всё
    python3 scripts/seed_worksheet_templates.py --only motion_half  # подмножество по подстроке
    python3 scripts/seed_worksheet_templates.py --preview           # только примеры, без записи
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.catalogue import catalogue_module_ids  # noqa: E402
from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from problemgen.template_studio.service import TemplateStudioService  # noqa: E402
from problemgen.template_studio.storage import TemplateStudioStore  # noqa: E402


LIBRARY_ROOT = PROJECT_ROOT / "data" / "template_studio" / "library"
# Поля, которые сервис проставляет сам или которые нельзя менять через update_draft.
NON_EDITABLE_KEYS = {"schema_version", "template_id", "math_notes"}
REQUIRED_KEYS = {
    "template_id", "module_id", "candidate_template_text",
    "parameter_schema", "answer_expression", "answer_type", "solver_strategy",
}


def load_library(only: str | None = None) -> list[dict[str, Any]]:
    """Прочитать шаблоны из библиотеки JSON и проверить обязательные поля."""
    if not LIBRARY_ROOT.is_dir():
        raise SystemExit(f"Нет библиотеки шаблонов: {LIBRARY_ROOT}")
    templates: list[dict[str, Any]] = []
    for path in sorted(LIBRARY_ROOT.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_KEYS - set(payload)
        if missing:
            raise SystemExit(f"{path.name}: нет обязательных полей: {', '.join(sorted(missing))}.")
        if payload["template_id"] != path.stem:
            raise SystemExit(f"{path.name}: template_id должен совпадать с именем файла.")
        if only and only not in payload["template_id"]:
            continue
        templates.append(payload)
    if not templates:
        raise SystemExit("Под фильтр не попал ни один шаблон.")
    return templates


def preview(template: dict[str, Any], count: int) -> None:
    """Показать несколько примеров по шаблону без записи на диск."""
    print(f"\n=== {template['template_id']} ===")
    for seed in range(count):
        generated = generate_active_template(template, random.Random(seed))
        print(f"[seed {seed}] {generated['rendered_problem']}")
        print(f"           Ответ: {generated['answer_text']}   (raw {generated['answer']})")


def publish(service: TemplateStudioService, store: TemplateStudioStore, template: dict[str, Any]) -> bool:
    """Прогнать шаблон через draft → validate → activate."""
    known_modules = catalogue_module_ids()
    active_ids = {item.get("template_id") for item in store.load_active_templates()}
    if template["template_id"] in active_ids:
        store.archive_active(template["template_id"])

    draft = service.create_from_analysis({
        "original_text": template["candidate_template_text"],
        "template_id": template["template_id"],
        "module_id": template["module_id"],
        "source_problem_number": str(template.get("source_metadata", {}).get("problem_number") or ""),
        "source_filename": str(template.get("source_metadata", {}).get("filename") or ""),
    })
    changes = {key: value for key, value in template.items() if key not in NON_EDITABLE_KEYS}
    service.update_draft(draft["draft_id"], changes)

    report = service.validate(draft["draft_id"], known_module_ids=known_modules, existing_template_ids=set())
    for check in report["checks"]:
        print(f"  [{'OK  ' if check['passed'] else 'FAIL'}] {check['label']}: {check['message']}")
    if not report["passed"]:
        return False
    service.activate(draft["draft_id"], known_module_ids=known_modules, existing_template_ids=set())
    return True


def parse_args() -> argparse.Namespace:
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Опубликовать шаблоны 15-минутки из JSON-библиотеки.")
    parser.add_argument("--preview", action="store_true",
                        help="Только показать примеры, ничего не сохранять.")
    parser.add_argument("--only", default=None,
                        help="Публиковать шаблоны, чей template_id содержит подстроку.")
    parser.add_argument("--count", type=int, default=3, help="Сколько примеров показать на шаблон.")
    return parser.parse_args()


def main() -> None:
    """Опубликовать или показать шаблоны из библиотеки."""
    args = parse_args()
    templates = load_library(args.only)

    if args.preview:
        for template in templates:
            preview(template, args.count)
        return

    store = TemplateStudioStore()
    service = TemplateStudioService(store=store)
    failed: list[str] = []
    for template in templates:
        print(f"\n=== {template['template_id']} ===")
        if publish(service, store, template):
            preview(template, args.count)
        else:
            failed.append(template["template_id"])

    print(f"\nАктивных шаблонов: {len(store.load_active_templates())}")
    if failed:
        raise SystemExit("Не прошли валидацию: " + ", ".join(failed))


if __name__ == "__main__":
    main()
