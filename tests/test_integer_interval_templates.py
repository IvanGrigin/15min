from __future__ import annotations

import random
import unittest

from problemgen.generation.integer_interval_templates import (
    IntegerIntervalTemplateError,
    count_even_inclusive,
    count_parity_inclusive,
    count_parity_with_digit,
    generate_integer_interval_problem,
    generate_integer_interval_problem_from_module,
    load_integer_interval_templates,
    source_integer_interval_problem_numbers,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class IntegerIntervalTemplatesTests(unittest.TestCase):
    def test_source_accounting_and_duplicate_grouping(self) -> None:
        templates = load_integer_interval_templates()
        numbers = [number for item in templates for number in item["source_problem_numbers"]]
        self.assertEqual(set(numbers), source_integer_interval_problem_numbers())
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(templates), 5)
        self.assertEqual(next(item for item in templates if item["id"] == "integer_interval_002_even_inclusive")["source_problem_numbers"], [98, 103, 889, 894, 1210, 1410])

    def test_endpoint_parity_combinations_and_inclusion(self) -> None:
        cases = [(3, 9), (3, 10), (4, 9), (4, 10)]
        for lower, upper in cases:
            self.assertEqual(count_even_inclusive(lower, upper), sum(number % 2 == 0 for number in range(lower, upper + 1)))
            self.assertEqual(count_parity_inclusive(lower, upper, "odd"), sum(number % 2 for number in range(lower, upper + 1)))
        self.assertEqual(count_parity_inclusive(4, 10, "odd"), 3)
        self.assertEqual(count_parity_inclusive(7, 7, "odd"), 1)

    def test_digit_condition_counts_numbers_once(self) -> None:
        self.assertEqual(count_parity_with_digit(1, 1000, "odd", 7), sum(number % 2 and "7" in str(number) for number in range(1, 1001)))
        self.assertEqual(count_parity_with_digit(77, 77, "odd", 7), 1)
        self.assertEqual(count_parity_with_digit(707, 707, "odd", 7), 1)
        self.assertEqual(count_parity_with_digit(1000, 1000, "even", 1), 1)

    def test_every_template_generates_500_exact_instances(self) -> None:
        for template in load_integer_interval_templates():
            texts: set[str] = set()
            for seed in range(500):
                generated = generate_integer_interval_problem(template["id"], seed=seed)
                texts.add(generated.problem_text)
                params = generated.parameters
                self.assertNotIn("{", generated.problem_text)
                self.assertIsInstance(generated.answer, int)
                self.assertGreaterEqual(generated.answer, 0)
                lower, upper = params["lower_bound"], params["upper_bound"]
                if params["interval_type"] == "inclusive":
                    self.assertLessEqual(lower, upper)
                else:
                    self.assertEqual(generated.answer, len(list(range(lower + 1, upper))))
                if "digit" in params:
                    brute = sum(number % 2 == (0 if params["parity"] == "even" else 1) and str(params["digit"]) in str(number) for number in range(lower, upper + 1))
                    self.assertEqual(generated.answer, brute)
                elif "parity" in params:
                    self.assertEqual(generated.answer, sum(number % 2 == (0 if params["parity"] == "even" else 1) for number in range(lower, upper + 1)))
            self.assertGreater(len(texts), 1)

    def test_module_mixed_worksheet_and_errors(self) -> None:
        self.assertEqual(generate_integer_interval_problem_from_module("integer_interval_counting", rng=random.Random(4)), generate_integer_interval_problem_from_module("integer_interval_counting", rng=random.Random(4)))
        modules = ["arithmetic", "equations", "systems_of_equations", "sequences_progressions_and_sums", "integer_interval_counting"]
        first = generate_combined_worksheet_by_modules(modules, seed=20260717)
        self.assertEqual(first, generate_combined_worksheet_by_modules(modules, seed=20260717))
        self.assertEqual(first["selected_templates"][-1]["module_id"], "integer_interval_counting")
        with self.assertRaises(IntegerIntervalTemplateError):
            generate_integer_interval_problem("unknown", seed=1)
        with self.assertRaises(IntegerIntervalTemplateError):
            generate_integer_interval_problem_from_module("arithmetic", rng=random.Random(1))


if __name__ == "__main__":
    unittest.main()
