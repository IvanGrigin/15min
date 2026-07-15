from __future__ import annotations

import random
import unittest

from problemgen.generation.arithmetic_templates import load_arithmetic_templates
from problemgen.generation.comparison_templates import (
    ComparisonTemplateError,
    generate_comparison_problem,
    generate_comparison_problem_from_module,
    load_approved_characters,
    load_comparison_templates,
    source_comparison_problem_numbers,
    two_digit_numbers_containing_digit,
)
from problemgen.generation.equation_templates import generate_equation_problem_from_module
from problemgen.generation.system_equation_templates import generate_system_equation_problem_from_module
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class ComparisonTemplatesTests(unittest.TestCase):
    def test_every_source_problem_number_is_accounted_for_once(self) -> None:
        numbers: list[int] = []
        for template in load_comparison_templates():
            numbers.extend(template["source_problem_numbers"])
        self.assertEqual(set(numbers), source_comparison_problem_numbers())
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(numbers), 25)

    def test_template_ids_are_unique_and_both_sources_are_present(self) -> None:
        templates = load_comparison_templates()
        ids = [template["id"] for template in templates]
        self.assertEqual(len(ids), len(set(ids)))
        all_numbers = {number for template in templates for number in template["source_problem_numbers"]}
        self.assertIn(67, all_numbers)
        self.assertIn(1164, all_numbers)

    def test_digit_enumeration_counts_each_two_digit_number_once(self) -> None:
        self.assertEqual(two_digit_numbers_containing_digit(7).count(77), 1)
        self.assertTrue(all(10 <= number <= 99 for number in two_digit_numbers_containing_digit(5)))
        self.assertEqual(sum(two_digit_numbers_containing_digit(7)), 1181)

    def test_every_template_generates_200_valid_instances(self) -> None:
        failures: list[str] = []
        for template in load_comparison_templates():
            generated_texts: set[str] = set()
            for seed in range(200):
                try:
                    generated = generate_comparison_problem(template["id"], seed=seed)
                    generated_texts.add(generated.problem_text)
                    self.assertNotIn("{", generated.problem_text)
                    self.assertNotIn("}", generated.problem_text)
                    self.assertNotIn("+ -", generated.problem_text)
                    self.assertNotIn("- -", generated.problem_text)
                    self.assertIsInstance(generated.answer["difference"], int)
                    if template["generation_strategy"] == "exact_quotient_comparison":
                        p = generated.parameters
                        self.assertEqual(p["dividend_1"] % p["divisor_1"], 0)
                        self.assertEqual(p["dividend_2"] % p["divisor_2"], 0)
                    if template["generation_strategy"] == "digit_sum_characters":
                        p = generated.parameters
                        self.assertEqual(p["digit_1_sum"], sum(two_digit_numbers_containing_digit(p["digit_1"])))
                        self.assertEqual(p["digit_2_sum"], sum(two_digit_numbers_containing_digit(p["digit_2"])))
                except Exception as error:  # noqa: BLE001 - тест собирает все хрупкие случаи.
                    failures.append(f"{template['id']}@{seed}: {error}")
            self.assertFalse(generated_texts <= set(template.get("source_examples", [])))
        self.assertEqual(failures, [])

    def test_character_templates_use_one_approved_universe(self) -> None:
        approved = load_approved_characters()
        generated = generate_comparison_problem("comparison_013", seed=20260715)
        self.assertIsNotNone(generated.universe)
        self.assertIn(generated.universe, approved)
        self.assertEqual(len(generated.characters or []), 2)
        self.assertEqual(len(set(generated.characters or [])), 2)
        approved_names = {character.name for character in approved[generated.universe or ""]}
        self.assertTrue(set(generated.characters or []) <= approved_names)
        second = generate_comparison_problem("comparison_013", seed=20260715)
        self.assertEqual(generated.problem_text, second.problem_text)
        self.assertEqual(generated.characters, second.characters)

    def test_non_character_templates_remain_character_free(self) -> None:
        generated = generate_comparison_problem("comparison_006", seed=1)
        self.assertIsNone(generated.universe)
        self.assertIsNone(generated.characters)

    def test_module_generation_and_invalid_ids(self) -> None:
        generated = generate_comparison_problem_from_module("comparison_of_numbers_and_expressions", rng=random.Random(1))
        self.assertEqual(generated.module, "comparison_of_numbers_and_expressions")
        with self.assertRaises(ComparisonTemplateError):
            generate_comparison_problem("no_such_template", seed=1)
        with self.assertRaises(ComparisonTemplateError):
            generate_comparison_problem_from_module("geometry", rng=random.Random(1))

    def test_regression_existing_modules_still_generate(self) -> None:
        self.assertGreater(len(load_arithmetic_templates()), 0)
        self.assertEqual(generate_equation_problem_from_module("equations", rng=random.Random(1)).module, "equations")
        self.assertEqual(
            generate_system_equation_problem_from_module("systems_of_equations", rng=random.Random(1)).module,
            "systems_of_equations",
        )

    def test_mixed_worksheet_can_contain_all_modules(self) -> None:
        modules = [
            "arithmetic",
            "equations",
            "systems_of_equations",
            "comparison_of_numbers_and_expressions",
            "comparison_of_numbers_and_expressions",
        ]
        first = generate_combined_worksheet_by_modules(modules, seed=20260715)
        second = generate_combined_worksheet_by_modules(modules, seed=20260715)
        self.assertEqual(first, second)
        self.assertEqual([problem["module_id"] for problem in first["selected_templates"]], modules)
        comparison_answers = [
            problem["answer"]
            for problem in first["selected_templates"]
            if problem["module_id"] == "comparison_of_numbers_and_expressions"
        ]
        self.assertTrue(all(isinstance(answer, str) and answer for answer in comparison_answers))


if __name__ == "__main__":
    unittest.main()
