"""Replace one leaf's bridge templates with supplied authored templates.

The JSON payload is read from stdin.  The script removes only entries with its
``source_tree_leaf``, appends the authored entries, and updates the matching
worklist records in the same operation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data/templates/problem_templates.json"
WORKLIST_PATH = ROOT / "data/source_index/per_task_template_worklist.json"


def _read_payload() -> dict[str, Any]:
    payload = json.load(sys.stdin)
    required = {"leaf_id", "templates", "primary_template_id", "notes"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"В payload не хватает полей: {', '.join(sorted(missing))}.")
    if not payload["templates"]:
        raise ValueError("Нужен хотя бы один авторский шаблон.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Проверить payload, не меняя файлы.")
    args = parser.parse_args()
    payload = _read_payload()
    leaf_id = payload["leaf_id"]
    templates = payload["templates"]
    if any(template.get("source_tree_leaf") != leaf_id for template in templates):
        raise ValueError("У каждого нового шаблона source_tree_leaf должен совпадать с leaf_id.")
    primary = next((template for template in templates if template["template_id"] == payload["primary_template_id"]), None)
    if primary is None:
        raise ValueError("primary_template_id должен указывать на один из новых шаблонов.")
    if args.check:
        print(f"Payload для {leaf_id}: {len(templates)} шаблона(ов), основной {primary['template_id']}.")
        return

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["templates"] = [
        template for template in catalog["templates"]
        if template.get("source_tree_leaf") != leaf_id
    ]
    catalog["templates"].extend(templates)
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    worklist = json.loads(WORKLIST_PATH.read_text(encoding="utf-8"))
    completed = 0
    for task in worklist["tasks"]:
        if task["leaf_id"] != leaf_id:
            continue
        task.update(
            template_text=primary["template_text"],
            number_strategy=primary["number_strategy"],
            answer_formula=primary["answer_formula"],
            answer_type=primary.get("answer_type", "number"),
            notes=payload["notes"],
            status="done",
        )
        completed += 1
    worklist["tasks_done"] = sum(task["status"] == "done" for task in worklist["tasks"])
    WORKLIST_PATH.write_text(json.dumps(worklist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{leaf_id}: добавлено {len(templates)} шаблона(ов), done: {completed}.")


if __name__ == "__main__":
    main()
