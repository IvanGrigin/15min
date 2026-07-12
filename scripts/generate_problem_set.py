from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.template_generator import generate_problem_from_template
from problemgen.worksheet.service import validate_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать набор из пяти задач по JSON-списку тем.")
    parser.add_argument("--items", required=True, help="JSON со списком из 5 объектов module/difficulty.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    items = validate_items(json.loads(args.items))
    rng = random.Random(args.seed)
    problems = [
        generate_problem_from_template(item["module"], item["difficulty"], rng=rng, index=index).to_dict()
        for index, item in enumerate(items, start=1)
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"problems": problems}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Problems JSON: {output}")


if __name__ == "__main__":
    main()
