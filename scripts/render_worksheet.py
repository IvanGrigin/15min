from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.io.worksheet_renderer import render_worksheet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Рендер листа с задачами по JSON-шаблону."
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Путь к JSON-шаблону листа.",
    )
    parser.add_argument(
        "--problems",
        required=True,
        help="Путь к JSON-файлу со списком задач или bundle с полем problems.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Путь к итоговому PDF или PNG.",
    )
    parser.add_argument("--surname", default="", help="Фамилия для верхнего поля.")
    parser.add_argument("--name", default="", help="Имя для верхнего поля.")
    parser.add_argument("--date", default=None, help="Дата в верхнем правом углу.")
    parser.add_argument("--logo-path", default="", help="Путь к картинке в верхнем правом блоке.")
    parser.add_argument("--qr-path", default="", help="Путь к QR-коду в нижнем правом блоке.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = render_worksheet(
        template_path=args.template,
        problems_path=args.problems,
        output_path=args.output,
        surname=args.surname,
        name=args.name,
        date_text=args.date,
        logo_path=args.logo_path,
        qr_path=args.qr_path,
    )
    print(f"Worksheet rendered: {output_path}")


if __name__ == "__main__":
    main()
