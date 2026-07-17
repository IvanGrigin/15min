from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.integer_interval_templates import generate_integer_interval_problem, load_integer_interval_templates


def main() -> None:
    templates = load_integer_interval_templates()
    for template in templates:
        for seed in range(500):
            generate_integer_interval_problem(str(template["id"]), seed=seed)
    print(f"OK: {len(templates)} шаблонов, 500 deterministic-прогонов на каждый.")


if __name__ == "__main__":
    main()
