"""Кто из шаблонов уже заявил задачу корпуса.

Трижды за волну заготовленный шаблон оказывался повтором существующего:
задача числилась непокрытой просто потому, что в корпусе она записана
другими словами. Проверять номер до написания шаблона — дешевле, чем
удалять готовый.

    python3 tools/claimed_tasks.py 1152 465 598
    python3 tools/claimed_tasks.py --all | less
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[1] / "data" / "template_studio" / "library"


def claims() -> dict[str, list[str]]:
    """Номер задачи → шаблоны, которые на неё ссылаются."""
    found: dict[str, list[str]] = {}
    for path in sorted(LIBRARY.glob("*.json")):
        template = json.loads(path.read_text(encoding="utf-8"))
        source = template.get("source_metadata") or {}
        for number in re.findall(r"\d+", str(source.get("problem_number", ""))):
            found.setdefault(number, []).append(template["template_id"])
    return found


def main() -> None:
    found = claims()
    arguments = sys.argv[1:]
    if not arguments or arguments[0] == "--all":
        for number in sorted(found, key=int):
            print(f"{number}: {', '.join(found[number])}")
        return
    for number in arguments:
        owners = found.get(number)
        print(f"{number}: {', '.join(owners) if owners else 'свободна'}")


if __name__ == "__main__":
    main()
