"""Компактная выжимка очереди на проверку человеком.

Цель — чтобы проверяющий (человек или сильная модель) читал сотни токенов
на шаблон вместо тысяч: только то, по чему принимается решение.

    python3 scripts/review_queue.py                # дайджест incoming/
    python3 scripts/review_queue.py --examples 5   # больше примеров
    python3 scripts/review_queue.py --rejected     # что и почему не прошло
    python3 scripts/review_queue.py --accept <id>  # перенести в library/
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402

STUDIO_ROOT = PROJECT_ROOT / "data" / "template_studio"
INCOMING = STUDIO_ROOT / "incoming"
REJECTED = STUDIO_ROOT / "rejected"
LIBRARY = STUDIO_ROOT / "library"


def digest(template: dict[str, Any], examples: int) -> str:
    lines = [f"### {template['template_id']}  [{template.get('module_id')}]"]
    source = template.get("source_metadata", {})
    lines.append(f"источник: задачи {source.get('problem_number', '—')}")

    notes = template.get("math_notes") or {}
    if notes.get("structure"):
        lines.append(f"структура: {notes['structure']}")
    for step in (notes.get("math") or [])[:6]:
        lines.append(f"  математика: {step}")

    schema = template.get("parameter_schema", {})
    compact = ", ".join(
        f"{name}:{rule.get('type')}"
        + (f"[{rule.get('min')}..{rule.get('max')}]" if "min" in rule else "")
        for name, rule in schema.items()
    )
    lines.append(f"параметры: {compact}")
    if template.get("derived_values"):
        lines.append("derived: " + "; ".join(f"{k} = {v}" for k, v in template["derived_values"].items()))
    lines.append(f"ответ: {template.get('answer_expression')}  ({template.get('answer_type')})")
    constraints = template.get("constraints") or []
    lines.append(f"constraints ({len(constraints)}): " + "; ".join(constraints) if constraints
                 else "constraints: НЕТ — проверь, точно ли не нужны")

    ok = 0
    for seed in range(examples):
        try:
            generated = generate_active_template(template, random.Random(seed))
        except Exception as error:
            lines.append(f"  [seed {seed}] ОШИБКА: {error}")
            continue
        ok += 1
        lines.append(f"  [{seed}] {generated['rendered_problem']}")
        lines.append(f"       -> {generated.get('answer_text') or generated['answer']}")
    lines.append(f"сгенерировано без ошибок: {ok} из {examples}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Выжимка очереди на проверку.")
    parser.add_argument("--examples", type=int, default=3)
    parser.add_argument("--rejected", action="store_true", help="Показать отклонённые и причины.")
    parser.add_argument("--accept", default=None, help="Перенести шаблон из incoming в library.")
    args = parser.parse_args()

    if args.accept:
        source = INCOMING / f"{args.accept}.json"
        if not source.is_file():
            raise SystemExit(f"Нет файла {source}")
        LIBRARY.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(LIBRARY / source.name))
        print(f"Принято в библиотеку: {source.name}. Дальше нужен тест-решатель и публикация.")
        return

    if args.rejected:
        paths = sorted(REJECTED.glob("*.json"))
        print(f"Отклонено: {len(paths)}\n")
        for path in paths:
            record = json.loads(path.read_text(encoding="utf-8"))
            print(f"### {record['template_id']} — задачи {', '.join(record.get('source_problems', []))}")
            for attempt in record.get("attempts", []):
                print(f"  попытка {attempt['n']}: {attempt.get('error')}")
            print()
        return

    paths = sorted(INCOMING.glob("*.json"))
    print(f"На проверке: {len(paths)} шаблонов\n")
    for path in paths:
        print(digest(json.loads(path.read_text(encoding="utf-8")), args.examples))
        print()


if __name__ == "__main__":
    main()
