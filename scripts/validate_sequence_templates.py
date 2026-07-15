from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.sequence_templates import generate_sequence_problem, load_sequence_templates


def main() -> None:
    templates = load_sequence_templates()
    for template in templates:
        for seed in range(200):
            generate_sequence_problem(str(template["id"]), seed=seed)
    print(f"OK: {len(templates)} шаблонов, 200 deterministic-прогонов на каждый.")


if __name__ == "__main__":
    main()
