from __future__ import annotations

import math
import unittest

from problemgen.generation.arithmetic_templates import (
    SOURCE_PROBLEM_NUMBERS,
    ArithmeticTemplateError,
    generate_arithmetic_problem,
    generate_arithmetic_worksheet,
    generate_arithmetic_worksheet_by_modules,
    load_arithmetic_templates,
)


class ArithmeticTemplatesTests(unittest.TestCase):
    def test_every_source_problem_number_is_accounted_for_once(self) -> None:
        numbers: list[int] = []
        for template in load_arithmetic_templates():
            numbers.extend(template["source_problem_numbers"])
        self.assertEqual(set(numbers), SOURCE_PROBLEM_NUMBERS)
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(numbers), 75)

    def test_template_ids_are_unique(self) -> None:
        ids = [template["id"] for template in load_arithmetic_templates()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_template_generates_valid_integer_answers_for_100_seeds(self) -> None:
        failures: list[str] = []
        for template in load_arithmetic_templates():
            for seed in range(100):
                try:
                    generated = generate_arithmetic_problem(template["id"], seed=seed)
                except Exception as error:  # noqa: BLE001 - тест собирает все хрупкие случаи.
                    failures.append(f"{template['id']}@{seed}: {error}")
                    continue
                self.assertNotIn("{", generated.problem_text)
                self.assertTrue(isinstance(generated.answer, int) or all(isinstance(item, int) for item in generated.answer))
        self.assertEqual(failures, [])

    def test_distributed_common_factor_keeps_nontrivial_gcd(self) -> None:
        generated = generate_arithmetic_problem("arithmetic_019", seed=17)
        values = generated.parameters
        self.assertGreater(math.gcd(values["term_1"], values["term_2"], values["term_3"]), 1)

    def test_growing_even_gaps_preserves_first_unit_gap_then_even_gaps(self) -> None:
        generated = generate_arithmetic_problem("arithmetic_007", seed=5)
        terms = generated.parameters["terms_full"]
        gaps = [right - left for left, right in zip(terms, terms[1:], strict=False)]
        self.assertEqual(gaps[0], 1)
        self.assertTrue(all(gap % 2 == 0 for gap in gaps[1:]))
        self.assertEqual(gaps[1:], list(range(gaps[1], gaps[1] + 2 * len(gaps[1:]), 2)))

    def test_medium_step_progression_is_really_step_three(self) -> None:
        generated = generate_arithmetic_problem("arithmetic_014", seed=8)
        terms = generated.parameters["terms_full"]
        self.assertTrue(all(right - left == 3 for left, right in zip(terms, terms[1:], strict=False)))

    def test_split_subproblem_templates_return_expected_answer_counts(self) -> None:
        expected_lengths = {
            "arithmetic_034": 2,
            "arithmetic_036": 2,
            "arithmetic_037": 2,
            "arithmetic_038": 2,
            "arithmetic_039": 1,
        }
        for template_id, expected_length in expected_lengths.items():
            generated = generate_arithmetic_problem(template_id, seed=13)
            if expected_length == 1:
                self.assertIsInstance(generated.answer, int)
            else:
                self.assertIsInstance(generated.answer, list)
                self.assertEqual(len(generated.answer), expected_length)

    def test_worksheet_requires_exactly_five_templates(self) -> None:
        with self.assertRaises(ArithmeticTemplateError):
            generate_arithmetic_worksheet(["arithmetic_001"], seed=1)

    def test_worksheet_rejects_duplicate_templates(self) -> None:
        with self.assertRaises(ArithmeticTemplateError):
            generate_arithmetic_worksheet(["arithmetic_001"] * 5, seed=1)

    def test_worksheet_generates_exactly_five_problems(self) -> None:
        worksheet = generate_arithmetic_worksheet(
            ["arithmetic_001", "arithmetic_003", "arithmetic_017", "arithmetic_019", "arithmetic_022"],
            seed=20260715,
        )
        self.assertEqual(len(worksheet["selected_templates"]), 5)
        self.assertTrue(all("answer" in problem for problem in worksheet["selected_templates"]))

    def test_module_worksheet_allows_same_module_in_all_slots(self) -> None:
        worksheet = generate_arithmetic_worksheet_by_modules(["arithmetic"] * 5, seed=20260715)
        self.assertEqual(worksheet["selected_modules"], ["arithmetic"] * 5)
        self.assertEqual(len(worksheet["selected_templates"]), 5)
        self.assertTrue(all(problem["module_id"] == "arithmetic" for problem in worksheet["selected_templates"]))
        self.assertGreaterEqual(len({problem["template_id"] for problem in worksheet["selected_templates"]}), 1)

    def test_module_worksheet_rejects_unknown_module(self) -> None:
        with self.assertRaises(ArithmeticTemplateError):
            generate_arithmetic_worksheet_by_modules(["geometry"] * 5, seed=1)

    def test_invalid_template_id_returns_clear_error(self) -> None:
        with self.assertRaises(ArithmeticTemplateError):
            generate_arithmetic_problem("no_such_template", seed=1)


if __name__ == "__main__":
    unittest.main()
