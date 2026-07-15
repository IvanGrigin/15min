from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.equation_templates import generate_equation_problem, load_equation_templates


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверить генерацию шаблонов уравнений.")
    parser.add_argument("--seeds", type=int, default=10, help="Сколько seed-значений проверять на каждый шаблон.")
    args = parser.parse_args()
    templates = load_equation_templates()
    failures: list[str] = []
    for template in templates:
        for seed in range(args.seeds):
            try:
                generated = generate_equation_problem(template["id"], seed=seed)
            except Exception as error:  # noqa: BLE001 - валидатор собирает все ошибки.
                failures.append(f"{template['id']}@{seed}: {error}")
                continue
            if "{" in generated.problem_text or "}" in generated.problem_text:
                failures.append(f"{template['id']}@{seed}: остался незаполненный плейсхолдер")
    if failures:
        print("Ошибки в шаблонах уравнений:")
        for failure in failures[:50]:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"Проверено шаблонов: {len(templates)}")
    print(f"Для каждого шаблона проверено seed-значений: {args.seeds}.")


if __name__ == "__main__":
    main()
