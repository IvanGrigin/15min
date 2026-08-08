"""Кто из шаблонов уже заявил задачу корпуса.

Трижды за волну заготовленный шаблон оказывался повтором существующего:
задача числилась непокрытой просто потому, что в корпусе она записана
другими словами. Проверять номер до написания шаблона — дешевле, чем
удалять готовый.

Номер сам по себе ничего не значит: **у каждого файла корпуса своя
нумерация.** Задача 38 в `docs/15_kalendar_…` — про четверги в марте,
а задача 38 в сводном файле — про вымышленный язык из букв И, В, А, Н.
Поэтому ответ всегда даётся с указанием файла, а искать можно и по номеру
сразу во всех файлах, и в одном названном.

    python3 tools/claimed_tasks.py 1152 465 598
    python3 tools/claimed_tasks.py --file docs/all_tasks_all_files.md 38
    python3 tools/claimed_tasks.py --all | less
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[1] / "data" / "template_studio" / "library"


def sources_of(template: dict) -> list[tuple[str, str]]:
    """Все ссылки шаблона на корпус: (файл, перечень номеров)."""
    meta = template.get("source_metadata") or {}
    found = [(str(meta.get("filename") or ""), str(meta.get("problem_number") or ""))]
    for extra in meta.get("additional_sources") or []:
        found.append((str((extra or {}).get("filename") or ""),
                      str((extra or {}).get("problem_number") or "")))
    return [(filename, numbers) for filename, numbers in found if filename and numbers.strip()]


def claims() -> dict[tuple[str, str], list[str]]:
    """(файл, номер) → шаблоны, которые на эту задачу ссылаются."""
    found: dict[tuple[str, str], list[str]] = {}
    for path in sorted(LIBRARY.glob("*.json")):
        template = json.loads(path.read_text(encoding="utf-8"))
        for filename, numbers in sources_of(template):
            for number in re.findall(r"\d+", numbers):
                found.setdefault((filename, number), []).append(template["template_id"])
    return found


def main() -> None:
    """Показать, какие шаблоны заявили названные задачи корпуса."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("numbers", nargs="*", help="номера задач корпуса")
    parser.add_argument("--file", default=None,
                        help="искать только в этом файле корпуса")
    parser.add_argument("--all", action="store_true", help="выписать все занятые задачи")
    arguments = parser.parse_args()

    found = claims()
    if arguments.all or not arguments.numbers:
        for (filename, number) in sorted(found, key=lambda key: (key[0], int(key[1]))):
            print(f"{Path(filename).name} {number}: {', '.join(found[(filename, number)])}")
        return

    for number in arguments.numbers:
        owners = [
            (filename, templates) for (filename, value), templates in found.items()
            if value == number and (arguments.file is None or filename == arguments.file)
        ]
        if not owners:
            where = f" в {Path(arguments.file).name}" if arguments.file else ""
            print(f"{number}: свободна{where}")
            continue
        for filename, templates in sorted(owners):
            print(f"{number} в {Path(filename).name}: {', '.join(templates)}")


if __name__ == "__main__":
    main()
