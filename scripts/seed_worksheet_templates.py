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


def branching_parameters(template: dict[str, Any]) -> dict[str, list[Any]]:
    """Параметры-развилки: choice, boolean и bundle, от которых зависит формулировка.

    Bundle здесь обязателен: он несёт целые связки «слово + число» (четверть,
    восьмая часть; фразы условий), и без добора его веток обязательный шаг
    «прочитать десять примеров глазами» систематически пропускал формулировки —
    строка «Покрытие веток» о них просто молчала.
    """
    schema = template.get("parameter_schema", {})
    branches: dict[str, list[Any]] = {}
    for name, rule in schema.items():
        if not isinstance(rule, dict):
            continue
        if rule.get("type") == "choice" and isinstance(rule.get("allowed_values"), list):
            values = rule["allowed_values"]
            if 2 <= len(values) <= 8:
                branches[name] = list(values)
        elif rule.get("type") == "bundle" and isinstance(rule.get("allowed_values"), list):
            values = rule["allowed_values"]
            if 2 <= len(values) <= 8 and all(isinstance(value, dict) for value in values):
                branches[name] = list(values)
        elif rule.get("type") == "boolean":
            branches[name] = [True, False]
    return branches


def branch_key(value: Any) -> Any:
    """Ключ ветки, пригодный для множества: bundle-словарь сериализуется."""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value.nom if hasattr(value, "nom") else value


def branch_label(value: Any) -> str:
    """Короткая подпись ветки для строки «[ветка …]»."""
    if isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return text if len(text) <= 60 else text[:57] + "…"
    return repr(value)


def preview(template: dict[str, Any], count: int) -> None:
    """Показать примеры по шаблону, покрыв каждое значение параметров-развилок.

    Обычные `count` сидов подряд могут показать одну и ту же ветку: если
    выбор переключает глагол, половина формулировок останется непрочитанной.
    Именно так в шаблоне про трамваи выжила ошибка управления — «на маршрут
    убрали» вместо «с маршрута убрали». Поэтому после обычных примеров
    добираются сиды, показывающие недостающие значения.
    """
    print(f"\n=== {template['template_id']} ===")
    branches = branching_parameters(template)
    seen: dict[str, set[Any]] = {name: set() for name in branches}

    def show(seed: int, note: str = "") -> None:
        generated = generate_active_template(template, random.Random(seed))
        for name in branches:
            seen[name].add(branch_key(generated["parameters"].get(name)))
        print(f"[seed {seed}]{note} {generated['rendered_problem']}")
        print(f"           Ответ: {generated['answer_text']}   (raw {generated['answer']})")

    for seed in range(count):
        show(seed)

    # Добираем недостающие ветки, чтобы автор увидел каждую формулировку.
    for name, values in branches.items():
        for value in values:
            if branch_key(value) in seen[name]:
                continue
            for seed in range(count, count + 400):
                generated = generate_active_template(template, random.Random(seed))
                if branch_key(generated["parameters"].get(name)) == branch_key(value):
                    show(seed, f" [ветка {name}={branch_label(value)}]")
                    break
            else:
                print(f"           ВНИМАНИЕ: ветка {name}={branch_label(value)} не встретилась за 400 сидов.")

    if branches:
        covered = ", ".join(f"{name}: {len(seen[name])} из {len(values)}"
                            for name, values in branches.items())
        print(f"           Покрытие веток — {covered}.")


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

    # Удалённый из библиотеки шаблон обязан исчезнуть и из активного каталога.
    # Иначе сайт продолжает выдавать задачу, которой в репозитории уже нет:
    # так после переименования очереди на сайте оставалась старая версия
    # с зашитыми пиратами и похлёбкой.
    if not args.only:
        in_library = {item["template_id"] for item in load_library()}
        stale = sorted(
            str(item.get("template_id"))
            for item in store.load_active_templates()
            if item.get("template_id") not in in_library
        )
        for template_id in stale:
            store.archive_active(template_id)
            print(f"Убран из активных (нет в библиотеке): {template_id}")

    print(f"\nАктивных шаблонов: {len(store.load_active_templates())}")
    if failed:
        raise SystemExit("Не прошли валидацию: " + ", ".join(failed))


if __name__ == "__main__":
    main()
