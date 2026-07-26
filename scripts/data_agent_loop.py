"""Пополнение словаря существительных по правилам склонения.

Правила (`scripts/declension_rules.py`) готовят все двенадцать форм, механические
проверки отсеивают невозможное, человек вычитывает компактную таблицу через
`scripts/data_review.py`. Языковая модель в этой роли не участвует: замер на
29 словах показал, что она путает творительный падеж с винительным
и предложный с дательным — см. `docs/DATA_PIPELINE.md`.

Правила не универсальны: 80 % точности там, где они уверены, и 28 % слов они
сами помечают как рискованные. Поэтому это заготовка, а не автоприём.

Запуск:
    python3 scripts/data_agent_loop.py --queue data/language/queue/nouns.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from declension_rules import CASES, decline, orthography_problems  # noqa: E402

NOUNS_PATH = PROJECT_ROOT / "data" / "language" / "nouns" / "russian_nouns.json"
STAGING_ROOT = PROJECT_ROOT / "data" / "language" / "staging"


def mechanical_problems(forms: dict[str, str], animate: bool) -> list[str]:
    """Нарушения правил русского языка, у которых нет исключений."""
    problems = orthography_problems(forms)
    expected = forms.get("gen_pl") if animate else forms.get("nom_pl")
    if forms.get("acc_pl") != expected:
        problems.append(
            f"acc_pl={forms.get('acc_pl')!r}: при animate={animate} должно быть {expected!r}"
        )
    if animate and forms.get("acc") != forms.get("gen"):
        problems.append("одушевлённое: винительный ед. ч. должен совпадать с родительным")
    return problems


def process(word: str, gender: str, animate: bool) -> dict[str, Any]:
    """Построить заготовку словоформ по правилам и отметить рискованные места."""
    rules = decline(word, gender, animate=animate)
    problems = (
        mechanical_problems(rules.forms, animate) if rules.forms
        else ["правила не распознали тип склонения"]
    )
    return {
        "word": word,
        "gender": gender,
        "animate": animate,
        "rules_confidence": rules.confidence,
        "rules_notes": list(rules.notes),
        "mechanical_problems": problems,
        "forms": rules.forms,
        "outcome": "needs_check" if (problems or rules.confidence == "low") else "draft_ok",
    }


def parse_args() -> argparse.Namespace:
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Заготовки словоформ по правилам склонения.")
    parser.add_argument("--queue", required=True, help="JSON со списком слов: word, gender, animate.")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    """Обработать очередь слов и разложить результат по файлам staging."""
    args = parse_args()
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))["words"]
    if args.limit:
        queue = queue[: args.limit]
    known = set(json.loads(NOUNS_PATH.read_text(encoding="utf-8"))["nouns"])

    records: list[dict[str, Any]] = []
    for index, item in enumerate(queue, start=1):
        word = item["word"]
        if word in known:
            print(f"[{index}/{len(queue)}] {word}: уже в словаре, пропуск")
            continue
        record = process(word, item["gender"], bool(item.get("animate", False)))
        records.append(record)
        mark = "заготовка" if record["outcome"] == "draft_ok" else "на проверку"
        note = "; ".join(record["rules_notes"] or record["mechanical_problems"])
        print(f"[{index}/{len(queue)}] {word}: {mark}" + (f" [{note}]" if note else ""))

    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    drafts = [record for record in records if record["outcome"] == "draft_ok"]
    checks = [record for record in records if record["outcome"] == "needs_check"]
    (STAGING_ROOT / f"agreed_{stamp}.json").write_text(
        json.dumps({"words": drafts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STAGING_ROOT / f"conflicts_{stamp}.json").write_text(
        json.dumps({"words": checks}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = len(records)
    print(f"\nОбработано: {total}")
    if total:
        print(f"  заготовок без замечаний: {len(drafts)} ({len(drafts) / total:.0%})")
        print(f"  требуют внимания: {len(checks)} ({len(checks) / total:.0%})")
    print("Дальше: python3 scripts/data_review.py")


if __name__ == "__main__":
    main()
