"""Расширенная проверка модуля отношений, долей и процентов."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.ratio_templates import generate_ratio_problem, load_ratio_templates


def main() -> None:
    templates = load_ratio_templates()
    runs = 0
    for template in templates:
        for seed in range(200):
            first = generate_ratio_problem(template["id"], seed=seed)
            second = generate_ratio_problem(template["id"], seed=seed)
            if first != second or not isinstance(first.answer, int):
                raise SystemExit(f"Ошибка template={template['id']}, seed={seed}")
            runs += 1
    print(f"OK: {len(templates)} шаблонов, {runs} детерминированных генераций")


if __name__ == "__main__":
    main()
