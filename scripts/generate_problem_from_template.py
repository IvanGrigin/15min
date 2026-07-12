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


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать одну задачу из статичного JSON-шаблона.")
    parser.add_argument("--module", required=True)
    parser.add_argument("--difficulty", required=True, type=int)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    problem = generate_problem_from_template(args.module, args.difficulty, rng=random.Random(args.seed))
    print(json.dumps(problem.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
