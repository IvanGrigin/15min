"""Проверяет 300 deterministic-экземпляров каждого шаблона модуля 09."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.factor_product_templates import (
    generate_factor_product_problem,
    load_factor_product_templates,
)


def main() -> None:
    templates = load_factor_product_templates()
    for template in templates:
        for seed in range(300):
            first = generate_factor_product_problem(template["id"], seed=seed)
            second = generate_factor_product_problem(template["id"], seed=seed)
            assert first == second
            assert isinstance(first.answer, int)
            assert "{" not in first.problem_text
    print(f"OK: {len(templates)} шаблонов, {len(templates) * 300} deterministic-прогонов.")


if __name__ == "__main__":
    main()
