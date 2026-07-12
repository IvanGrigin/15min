from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.worksheet import generate_worksheet_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Сгенерировать ученический лист по 5 уровням сложности."
    )
    parser.add_argument(
        "--difficulties",
        required=False,
        help="Пять чисел через запятую, например 1,3,5,7,10",
    )
    parser.add_argument(
        "--items",
        default=None,
        help="JSON со списком из 5 объектов: module и difficulty.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Опциональный seed для воспроизводимой генерации.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.items:
        import json
        artifact = generate_worksheet_artifacts(items=json.loads(args.items), seed=args.seed)
    elif args.difficulties:
        difficulties = [int(part.strip()) for part in args.difficulties.split(",") if part.strip()]
        artifact = generate_worksheet_artifacts(difficulties, seed=args.seed)
    else:
        raise SystemExit("Укажите --items или --difficulties.")
    print(f"PDF: {artifact.pdf_path}")
    print(f"Problems JSON: {artifact.student_json_path}")
    print(f"Answers JSON: {artifact.answers_json_path}")


if __name__ == "__main__":
    main()
