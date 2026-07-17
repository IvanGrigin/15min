"""Ручная 300-seed проверка активных digits-шаблонов."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.digits_templates import generate_digits_problem, load_digits_templates


def main() -> None:
    active = [item for item in load_digits_templates() if item["active"]]
    for template in active:
        for seed in range(300):
            first = generate_digits_problem(template["id"], seed=seed)
            second = generate_digits_problem(template["id"], seed=seed)
            assert first == second
            assert "{" not in first.problem_text
    print(f"OK: {len(active)} active templates, {len(active) * 300} deterministic instances")


if __name__ == "__main__":
    main()
