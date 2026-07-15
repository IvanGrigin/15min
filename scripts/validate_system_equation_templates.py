from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.system_equation_templates import (  # noqa: E402
    generate_system_equation_problem,
    load_system_equation_templates,
    solve_system,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверить генерацию шаблонов систем уравнений.")
    parser.add_argument("--instances", type=int, default=200, help="Сколько вариантов проверять на каждый шаблон.")
    args = parser.parse_args()
    failures: list[str] = []
    templates = load_system_equation_templates()
    for template in templates:
        for seed in range(args.instances):
            try:
                generated = generate_system_equation_problem(template["id"], seed=seed)
                p = generated.parameters
                x, y, determinant = solve_system(
                    p["x_coefficient_1"],
                    p["y_coefficient_1"],
                    p["right_side_1"],
                    p["x_coefficient_2"],
                    p["y_coefficient_2"],
                    p["right_side_2"],
                )
                if determinant == 0:
                    failures.append(f"{template['id']}@{seed}: нулевой определитель")
                if x.denominator != 1 or y.denominator != 1:
                    failures.append(f"{template['id']}@{seed}: дробный ответ")
                if int(x) != generated.answer["x"] or int(y) != generated.answer["y"]:
                    failures.append(f"{template['id']}@{seed}: ответ не совпал с независимым решением")
                bad_fragments = ("{", "}", "+ -", "- -", "1X", "-1X", "1Y", "-1Y")
                if any(fragment in generated.problem_text for fragment in bad_fragments):
                    failures.append(f"{template['id']}@{seed}: плохое отображение {generated.problem_text}")
            except Exception as error:  # noqa: BLE001 - валидатор собирает все ошибки.
                failures.append(f"{template['id']}@{seed}: {error}")
    if failures:
        print("Ошибки в шаблонах систем уравнений:")
        for failure in failures[:50]:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"Проверено шаблонов: {len(templates)}")
    print(f"Для каждого шаблона проверено вариантов: {args.instances}.")


if __name__ == "__main__":
    main()
