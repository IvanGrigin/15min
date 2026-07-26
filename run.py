"""Запуск локального сайта пятиминуток.

Из корня репозитория:
    python3 run.py                 # сайт пятиминуток
    python3 run.py --port 8099     # другой порт

Задачи берутся только из активных шаблонов Template Studio, где падежи, род
и согласование заданы данными. Старый сайт на 33 Python-генераторах вынесен
в ветку archive/legacy-python-generators — см. Docs/ARCHIVED_LEGACY.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Локальный сайт пятиминуток.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--legacy", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.legacy:
        raise SystemExit(
            "Старый сайт вынесен в ветку archive/legacy-python-generators и здесь недоступен.\n"
            "Почему направление закрыто — Docs/ARCHIVED_LEGACY.md.\n"
            "Посмотреть код архива:  git show archive/legacy-python-generators:problemgen/web/worksheet_site.py"
        )

    from problemgen.web.studio_site import serve

    serve(args.host, args.port)


if __name__ == "__main__":
    main()
