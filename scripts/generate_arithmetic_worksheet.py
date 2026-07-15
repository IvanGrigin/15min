from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.arithmetic_templates import generate_arithmetic_worksheet  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Сгенерировать JSON-лист из пяти арифметических шаблонов.")
    parser.add_argument(
        "--template-ids",
        default="arithmetic_001,arithmetic_003,arithmetic_017,arithmetic_019,arithmetic_022",
        help="Ровно пять id через запятую.",
    )
    parser.add_argument("--seed", type=int, default=12345, help="Seed для воспроизводимого варианта.")
    parser.add_argument(
        "--output",
        default="outputs/generated/arithmetic_worksheet_example.json",
        help="Куда сохранить JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template_ids = [part.strip() for part in args.template_ids.split(",") if part.strip()]
    worksheet = generate_arithmetic_worksheet(template_ids, seed=args.seed)
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(worksheet, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON: {output_path}")
    print(f"Problems: {len(worksheet['selected_templates'])}")


if __name__ == "__main__":
    main()
