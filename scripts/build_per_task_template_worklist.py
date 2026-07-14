"""Собирает единый ворклист для будущего написания точного шаблона и формулы
ответа под КАЖДУЮ задачу из read-only корпуса `Docs/all_tasks_all_files.md`.

Скрипт ничего не выдумывает: он только сводит вместе уже существующие данные —
текст задачи из корпуса и её тему/сложность из дерева `data/source_index/task_tree`
— и раскладывает по одному слоту на задачу с пустыми полями `template_text`,
`number_strategy`, `answer_formula`, которые предстоит заполнить вручную.

Запуск:
    python scripts/build_per_task_template_worklist.py

Результат перезаписывается идемпотентно, ранее заполненные вручную слоты (status
!= "todo") сохраняются — обновляются только известные из источников поля.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = PROJECT_ROOT / "Docs" / "all_tasks_all_files.md"
TREE_DIR = PROJECT_ROOT / "data" / "source_index" / "task_tree"
MANIFEST_PATH = TREE_DIR / "manifest.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "source_index" / "per_task_template_worklist.json"

_ITEM_RE = re.compile(r"^(\d+)\.\s+(.*)$")
_SOURCE_ROW_RE = re.compile(r"source_\d+")

# Грубая эвристика: какие задачи текущий движок (только + - * / и один числовой
# ответ) закрыть НЕ сможет без расширения. Нужна лишь для приоритизации.
_NEEDS_EXTENSION_MARKERS = (
    "день недел", "дня недел", "табло", "цифр", "сколько раз", "делит",
    "простых", "простое", "нод", "нок", "остат", "делен", "кратн",
    "сколько существует", "способ", "перестанов", "сочетан", "больше и на сколько",
    "какое из чисел больше", "чётн", "нечётн", "разряд", "сумма цифр",
    "разверт", "покрас", "координат", "площад", "периметр", "объ", "градус",
    "угол", "рукопожат", "диагонал",
)


def parse_corpus() -> dict[int, dict[str, object]]:
    items: dict[int, dict[str, object]] = {}
    current_source = ""
    for line_no, raw in enumerate(CORPUS_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip()
        if line.startswith("## "):
            current_source = line[3:].strip()
            continue
        match = _ITEM_RE.match(line)
        if match:
            items[int(match.group(1))] = {
                "text": match.group(2).strip(),
                "source_file": current_source,
                "source_line": line_no,
            }
    return items


def parse_tree() -> dict[int, dict[str, object]]:
    titles = {t["theme_id"]: t["title"] for t in json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["themes"]}
    mapping: dict[int, dict[str, object]] = {}
    for leaf in sorted(TREE_DIR.glob("*/*.md")):
        if leaf.name == "README.md":
            continue
        leaf_id = leaf.stem
        for raw in leaf.read_text(encoding="utf-8").splitlines():
            if "source_" not in raw or not raw.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in raw.strip().strip("|").split("|")]
            if len(cells) < 5 or not _SOURCE_ROW_RE.search(cells[1]):
                continue
            if not cells[0].isdigit():
                continue
            item_id = int(cells[0])
            mapping[item_id] = {
                "leaf_id": leaf_id,
                "leaf_title": titles.get(leaf_id, ""),
                "difficulty": int(cells[2]) if cells[2].isdigit() else None,
                "quality": cells[3],
                "preview": "|".join(cells[4:]).strip(),
            }
    return mapping


def classify_answer_engine(text: str) -> str:
    low = text.lower()
    if any(marker in low for marker in _NEEDS_EXTENSION_MARKERS):
        return "needs_extension"
    return "arithmetic_candidate"


def build() -> dict[str, object]:
    corpus = parse_corpus()
    tree = parse_tree()
    existing = {}
    if OUTPUT_PATH.exists():
        for entry in json.loads(OUTPUT_PATH.read_text(encoding="utf-8")).get("tasks", []):
            existing[entry["corpus_id"]] = entry

    tasks = []
    for cid in sorted(corpus):
        leaf = tree.get(cid, {})
        prev = existing.get(cid, {})
        keep_manual = prev.get("status") not in (None, "todo")
        tasks.append({
            "corpus_id": cid,
            "leaf_id": leaf.get("leaf_id"),
            "leaf_title": leaf.get("leaf_title"),
            "difficulty": leaf.get("difficulty"),
            "quality": leaf.get("quality"),
            "source_file": corpus[cid]["source_file"],
            "source_line": corpus[cid]["source_line"],
            "original_text": corpus[cid]["text"],
            "answer_engine_hint": classify_answer_engine(str(corpus[cid]["text"])),
            # --- поля для ручного заполнения ---
            "proposed_template_id": prev.get("proposed_template_id", (f"task_{cid:04d}_{leaf.get('leaf_id','x')}_v1")),
            "number_strategy": prev.get("number_strategy") if keep_manual else None,
            "template_text": prev.get("template_text") if keep_manual else None,
            "answer_formula": prev.get("answer_formula") if keep_manual else None,
            "answer_type": prev.get("answer_type") if keep_manual else None,
            "notes": prev.get("notes", "") if keep_manual else "",
            "status": prev.get("status", "todo") if keep_manual else "todo",
        })

    covered = sum(1 for t in tasks if t["leaf_id"])
    done = sum(1 for t in tasks if t["status"] == "done")
    return {
        "schema_version": 1,
        "purpose": "Один слот на каждую задачу корпуса для написания точного шаблона и формулы ответа.",
        "source_corpus": "Docs/all_tasks_all_files.md",
        "source_tree": "data/source_index/task_tree",
        "total_tasks": len(tasks),
        "tasks_mapped_to_leaf": covered,
        "tasks_done": done,
        "answer_engine_hint_counts": {
            k: sum(1 for t in tasks if t["answer_engine_hint"] == k)
            for k in ("arithmetic_candidate", "needs_extension")
        },
        "field_guide": {
            "template_text": "Строка с плейсхолдерами {var}; воспроизводит структуру задачи.",
            "number_strategy": "Имя функции @_number_strategy в template_generator.py, подбирающей числа.",
            "answer_formula": "Арифметическое выражение над переменными (текущий движок: + - * / и унарный минус).",
            "answer_type": "number | multi | text — для 'multi'/'text' движок нужно расширить.",
            "status": "todo -> in_progress -> done.",
        },
        "tasks": tasks,
    }


def main() -> None:
    payload = build()
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Готово: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Всего задач: {payload['total_tasks']}; привязано к листу: {payload['tasks_mapped_to_leaf']}; сделано: {payload['tasks_done']}")
    print("Оценка движка:", payload["answer_engine_hint_counts"])


if __name__ == "__main__":
    main()
