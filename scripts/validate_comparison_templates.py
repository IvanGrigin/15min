from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation.comparison_templates import (  # noqa: E402
    generate_comparison_problem,
    load_approved_characters,
    load_comparison_templates,
    two_digit_numbers_containing_digit,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверить генерацию шаблонов сравнения.")
    parser.add_argument("--instances", type=int, default=200, help="Сколько вариантов проверять на каждый шаблон.")
    args = parser.parse_args()
    templates = load_comparison_templates()
    approved = load_approved_characters()
    failures: list[str] = []
    for template in templates:
        generated_texts: set[str] = set()
        for seed in range(args.instances):
            try:
                generated = generate_comparison_problem(template["id"], seed=seed)
                generated_texts.add(generated.problem_text)
                if "{" in generated.problem_text or "}" in generated.problem_text:
                    failures.append(f"{template['id']}@{seed}: остался плейсхолдер")
                if "+ -" in generated.problem_text or "- -" in generated.problem_text:
                    failures.append(f"{template['id']}@{seed}: плохая комбинация знаков")
                if not isinstance(generated.answer.get("difference"), int):
                    failures.append(f"{template['id']}@{seed}: разность не целая")
                if template["generation_strategy"] == "exact_quotient_comparison":
                    p = generated.parameters
                    if p["dividend_1"] % p["divisor_1"] or p["dividend_2"] % p["divisor_2"]:
                        failures.append(f"{template['id']}@{seed}: деление не точное")
                if template["generation_strategy"] == "digit_sum_characters":
                    if generated.universe not in approved:
                        failures.append(f"{template['id']}@{seed}: неизвестная вселенная")
                    if not generated.characters or len(generated.characters) != 2 or len(set(generated.characters)) != 2:
                        failures.append(f"{template['id']}@{seed}: неверный набор персонажей")
                    approved_names = {character.name for character in approved[generated.universe or ""]}
                    if any(character not in approved_names for character in generated.characters or []):
                        failures.append(f"{template['id']}@{seed}: персонаж не из выбранной вселенной")
                    p = generated.parameters
                    if p["digit_1_sum"] != sum(two_digit_numbers_containing_digit(p["digit_1"])):
                        failures.append(f"{template['id']}@{seed}: неверная сумма для digit_1")
                    if p["digit_2_sum"] != sum(two_digit_numbers_containing_digit(p["digit_2"])):
                        failures.append(f"{template['id']}@{seed}: неверная сумма для digit_2")
            except Exception as error:  # noqa: BLE001 - валидатор собирает все ошибки.
                failures.append(f"{template['id']}@{seed}: {error}")
        source_examples = set(template.get("source_examples", []))
        if generated_texts and generated_texts <= source_examples:
            failures.append(f"{template['id']}: генератор возвращает только исходный пример")
    if failures:
        print("Ошибки в шаблонах сравнения:")
        for failure in failures[:80]:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"Проверено шаблонов: {len(templates)}")
    print(f"Для каждого шаблона проверено вариантов: {args.instances}.")


if __name__ == "__main__":
    main()
