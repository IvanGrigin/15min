from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.web.worksheet_site import run_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Запуск локального сайта для генерации листов с задачами.")
    parser.add_argument("--host", default="127.0.0.1", help="Хост для сайта.")
    parser.add_argument("--port", default=8090, type=int, help="Порт для сайта.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
