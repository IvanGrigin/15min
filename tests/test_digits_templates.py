from __future__ import annotations

import json
import random
import unittest

from problemgen.generation.digits_templates import (
    DigitsTemplateError,
    count_distinct_numbers_from_digit_multiset,
    count_n_digit_numbers_with_digit_sum,
    count_subsequence_methods,
    digit_occurrences_in_range,
    generate_digits_problem,
    load_digits_templates,
    source_digits_problem_numbers,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class DigitsTemplateTests(unittest.TestCase):
    def test_source_accounting_is_exact(self) -> None:
        templates = load_digits_templates()
        seen = [number for template in templates for number in template["source_problem_numbers"]]
        self.assertEqual(set(seen), source_digits_problem_numbers())
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(len(seen), 129)

    def test_digit_occurrences_include_repetitions_and_zero(self) -> None:
        self.assertEqual(digit_occurrences_in_range(22, 22, 2), 2)
        self.assertEqual(digit_occurrences_in_range(1, 20, 0), 2)

    def test_digit_sum_dp_matches_brute_force(self) -> None:
        for length in range(1, 5):
            for total in range(15):
                brute = sum(sum(map(int, str(number))) == total for number in range(10 ** (length - 1), 10**length))
                self.assertEqual(count_n_digit_numbers_with_digit_sum(length, total), brute)

    def test_permutations_and_subsequences_handle_duplicates(self) -> None:
        self.assertEqual(count_distinct_numbers_from_digit_multiset("1123"), 12)
        self.assertEqual(count_distinct_numbers_from_digit_multiset("011"), 2)
        self.assertEqual(count_subsequence_methods("111", "11"), 3)

    def test_active_templates_are_deterministic(self) -> None:
        for template in load_digits_templates():
            if template["active"]:
                self.assertEqual(generate_digits_problem(template["id"], seed=17), generate_digits_problem(template["id"], seed=17))
            else:
                with self.assertRaises(DigitsTemplateError):
                    generate_digits_problem(template["id"], seed=17)

    def test_character_templates_use_one_universe_and_distinct_roles(self) -> None:
        for template in load_digits_templates():
            if template["active"] and template["uses_characters"]:
                generated = generate_digits_problem(template["id"], seed=31)
                self.assertIsNotNone(generated.universe)
                self.assertEqual(len(generated.characters or []), template["required_character_count"])
                self.assertEqual(len(generated.characters or []), len(set(generated.characters or [])))

    def test_module_works_on_site_with_fixed_seed(self) -> None:
        modules = ["digits_number_notation_and_cryptarithms"] * 5
        self.assertEqual(generate_combined_worksheet_by_modules(modules, seed=239), generate_combined_worksheet_by_modules(modules, seed=239))


if __name__ == "__main__":
    unittest.main()
