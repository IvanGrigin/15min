from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.arithmetic_templates import (  # noqa: E402
    generate_arithmetic_problem,
    load_arithmetic_templates,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Проверить арифметические шаблоны на 100 seeded-прогонах.")
    parser.add_argument("--seeds", type=int, default=100, help="Сколько сидов проверить для каждого шаблона.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    templates = load_arithmetic_templates()
    failures: list[str] = []
    for template in templates:
        template_id = str(template["id"])
        for seed in range(args.seeds):
            try:
                generate_arithmetic_problem(template_id, seed=seed)
            except Exception as error:  # noqa: BLE001 - валидатор собирает полный список проблем.
                failures.append(f"{template_id}@seed={seed}: {error}")

    if failures:
        print("Ошибки арифметических шаблонов:")
        for failure in failures[:50]:
            print(f"- {failure}")
        raise SystemExit(1)

    covered = sum(len(template["source_problem_numbers"]) for template in templates)
    print(f"OK: {len(templates)} templates, {covered} source problem numbers, {args.seeds} seeds each.")


if __name__ == "__main__":
    main()
