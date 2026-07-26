"""Разбор расхождений между правилами и моделью — и приём данных в словарь.

Показывает только те формы, где две независимые деривации не сошлись:
одна строка на слово, слева вариант правил, справа вариант модели.

    python3 scripts/data_review.py                          # что накопилось
    python3 scripts/data_review.py --accept-agreed          # влить совпавшие в словарь
    python3 scripts/data_review.py --resolve стол=rules     # решить конфликт в пользу правил
    python3 scripts/data_review.py --resolve окно=llm       # ... или модели
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from declension_rules import CASES  # noqa: E402

NOUNS_PATH = PROJECT_ROOT / "data" / "language" / "nouns" / "russian_nouns.json"
STAGING_ROOT = PROJECT_ROOT / "data" / "language" / "staging"


def newest(prefix: str) -> Path | None:
    """Найти самый свежий файл staging с нужным префиксом."""
    paths = sorted(STAGING_ROOT.glob(f"{prefix}_*.json"))
    return paths[-1] if paths else None


def load(prefix: str) -> list[dict[str, Any]]:
    """Прочитать записи из свежего файла staging."""
    path = newest(prefix)
    return json.loads(path.read_text(encoding="utf-8"))["words"] if path else []


def add_to_dictionary(entries: list[tuple[str, str, bool, dict[str, str]]]) -> int:
    """Добавить проверенные слова в словарь существительных."""
    payload = json.loads(NOUNS_PATH.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    added = 0
    for word, gender, animate, forms in entries:
        if word in payload["nouns"]:
            continue
        payload["nouns"][word] = collections.OrderedDict([
            ("gender", gender), ("animate", animate), ("legs", None), ("tags", ["object"]),
            ("forms", collections.OrderedDict((case, forms[case]) for case in CASES)),
        ])
        added += 1
    payload["nouns"] = collections.OrderedDict(sorted(payload["nouns"].items()))
    NOUNS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def main() -> None:
    """Показать очередь на проверку или принять слова в словарь."""
    parser = argparse.ArgumentParser(description="Разбор данных от агента.")
    parser.add_argument("--accept-agreed", action="store_true")
    parser.add_argument("--resolve", action="append", default=[], metavar="СЛОВО=rules|llm")
    args = parser.parse_args()

    agreed, conflicts = load("agreed"), load("conflicts")

    if args.accept_agreed:
        added = add_to_dictionary([
            (record["word"], record["gender"], record["animate"], record["forms"]) for record in agreed
        ])
        print(f"Добавлено в словарь: {added} (из {len(agreed)} совпавших).")
        print("Прогоните tests/test_noun_dictionary_integrity.py — он проверит правила без исключений.")
        return

    if args.resolve:
        by_word = {record["word"]: record for record in conflicts}
        chosen = []
        for item in args.resolve:
            word, _, source = item.partition("=")
            if word not in by_word:
                raise SystemExit(f"{word}: нет в списке конфликтов")
            if source not in {"rules", "llm"}:
                raise SystemExit(f"{word}: источник должен быть rules или llm")
            record = by_word[word]
            chosen.append((word, record["gender"], record["animate"], record["forms"][source]))
        print(f"Добавлено в словарь: {add_to_dictionary(chosen)}")
        return

    print(f"Совпали две деривации: {len(agreed)}  (принять: --accept-agreed)")
    for record in agreed:
        forms = record["forms"]
        print(f"  {record['word']}: {forms['gen']} / {forms['nom_pl']} / {forms['gen_pl']}")

    print(f"\nРасхождения: {len(conflicts)}")
    for record in conflicts:
        note = f"  [{record.get('reason', '')}]"
        print(f"\n### {record['word']} ({record['gender']}, "
              f"{'одуш.' if record['animate'] else 'неодуш.'}){note}")
        for problem in record.get("mechanical_problems", []):
            print(f"    нарушено правило: {problem}")
        for case, pair in record.get("mismatches", {}).items():
            print(f"    {case:7} правила: {pair['rules']:<20} модель: {pair['llm']}")
        for note in record.get("rules_notes", []):
            print(f"    заметка правил: {note}")


if __name__ == "__main__":
    main()
