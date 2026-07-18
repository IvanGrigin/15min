from __future__ import annotations

import math
import random
import json
import unittest

from problemgen.generation.factor_product_templates import (
    FactorProductTemplateError,
    ACCOUNTING_PATH,
    STRATEGIES,
    generate_factor_product_problem,
    generate_factor_product_problem_from_module,
    load_factor_product_accounting,
    load_factor_product_templates,
    minimum_factor_sum,
    source_factor_product_problem_numbers,
    trailing_zeros_of_product,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


def _brute_minimum_factor_sum(target: int, restriction: str) -> int:
    def allowed(left: int, right: int) -> bool:
        if restriction == "any":
            return True
        if restriction == "one_odd":
            return left % 2 == 1 or right % 2 == 1
        if restriction == "both_even":
            return left % 2 == 0 and right % 2 == 0
        if restriction == "both_odd":
            return left % 2 == 1 and right % 2 == 1
        if restriction == "without_zero_digits":
            return "0" not in str(left) and "0" not in str(right)
        raise AssertionError(restriction)

    sums = [
        left + target // left
        for left in range(1, target + 1)
        if target % left == 0 and allowed(left, target // left)
    ]
    return min(sums) if sums else -1


class FactorProductTemplateTests(unittest.TestCase):
    def test_source_accounting_covers_all_31_unique_numbers_once(self) -> None:
        payload = json.loads(ACCOUNTING_PATH.read_text(encoding="utf-8"))
        records = load_factor_product_accounting()
        numbers = [record["source_problem_number"] for record in records]
        self.assertEqual(len(numbers), 31)
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(set(numbers), source_factor_product_problem_numbers())
        self.assertEqual(payload["original_numbered_entry_count"], 44)
        self.assertEqual(payload["removed_duplicate_count"], 13)
        self.assertEqual(payload["unique_source_count"], 31)

    def test_named_source_is_empty(self) -> None:
        named_numbers = source_factor_product_problem_numbers((
            __import__("pathlib").Path("docs/09_mnozhiteli_proizvedeniya_i_faktorialy_s_imenami_i_personazhami_deduplicated.md"),
        ))
        self.assertEqual(named_numbers, set())

    def test_manifest_links_active_sources_and_explains_exclusions(self) -> None:
        templates = load_factor_product_templates()
        template_ids = {template["id"] for template in templates}
        for record in load_factor_product_accounting():
            if record["status"] == "active_template":
                self.assertIn(record["template_id"], template_ids)
            else:
                self.assertTrue(record["status"].startswith("excluded_"))
                self.assertTrue(record["exclusion_reason"].strip())

    def test_runtime_schema_and_strategy_registration(self) -> None:
        ids: list[str] = []
        for template in load_factor_product_templates():
            ids.append(template["id"])
            self.assertEqual(template["module"], "factors_products_and_factorials")
            self.assertEqual(template["answer_type"], "integer")
            self.assertIn(template["generation_strategy"], STRATEGIES)
            self.assertNotIn("number_", template["render_template"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_factor_solver_matches_independent_enumeration(self) -> None:
        cases = [(36, "any"), (45, "one_odd"), (144, "both_even"), (225, "both_odd"), (1000, "without_zero_digits")]
        for target, restriction in cases:
            with self.subTest(target=target, restriction=restriction):
                self.assertEqual(minimum_factor_sum(target, restriction), _brute_minimum_factor_sum(target, restriction))

    def test_invalid_factor_and_interval_parameters_are_rejected(self) -> None:
        with self.assertRaises(FactorProductTemplateError):
            minimum_factor_sum(0, "any")
        with self.assertRaises(FactorProductTemplateError):
            minimum_factor_sum(12, "unknown")
        with self.assertRaises(FactorProductTemplateError):
            trailing_zeros_of_product(10, 5)

    def test_trailing_zero_solver_matches_direct_products_at_edges(self) -> None:
        for start, end in ((1, 1), (1, 10), (7, 38), (20, 50)):
            product = math.prod(range(start, end + 1))
            direct = len(str(product)) - len(str(product).rstrip("0"))
            self.assertEqual(trailing_zeros_of_product(start, end), direct)

    def test_every_strategy_has_20_exact_independently_verified_instances(self) -> None:
        for template in load_factor_product_templates():
            for seed in range(20):
                generated = generate_factor_product_problem(template["id"], seed=seed)
                self.assertIsInstance(generated.answer, int)
                self.assertNotIn("{", generated.problem_text)
                strategy = template["generation_strategy"]
                if strategy.startswith("factor_pair_min_sum"):
                    expected = _brute_minimum_factor_sum(
                        generated.parameters["target_product"],
                        generated.parameters["factor_restriction"],
                    )
                elif strategy == "factorial_value":
                    expected = math.prod(range(1, generated.parameters["factorial_argument"] + 1))
                else:
                    start = generated.parameters["start_value"]
                    end = generated.parameters["end_value"]
                    product = math.prod(range(start, end + 1))
                    expected = len(str(product)) - len(str(product).rstrip("0"))
                self.assertEqual(generated.answer, expected)

    def test_fixed_seed_and_module_selection_are_deterministic(self) -> None:
        template_id = "factor_pair_min_sum_one_odd"
        self.assertEqual(generate_factor_product_problem(template_id, seed=239), generate_factor_product_problem(template_id, seed=239))
        first = generate_factor_product_problem_from_module("factors_products_and_factorials", rng=random.Random(239))
        second = generate_factor_product_problem_from_module("factors_products_and_factorials", rng=random.Random(239))
        self.assertEqual(first, second)

    def test_runtime_selection_never_returns_excluded_inventory(self) -> None:
        active_ids = {template["id"] for template in load_factor_product_templates()}
        for seed in range(200):
            generated = generate_factor_product_problem_from_module(
                "factors_products_and_factorials", rng=random.Random(seed)
            )
            self.assertIn(generated.template_id, active_ids)

    def test_module_works_in_mixed_site_worksheet(self) -> None:
        modules = [
            "factors_products_and_factorials",
            "arithmetic",
            "digits_number_notation_and_cryptarithms",
            "divisibility_multiples_remainders_primes",
            "integer_interval_counting",
        ]
        first = generate_combined_worksheet_by_modules(modules, seed=909)
        second = generate_combined_worksheet_by_modules(modules, seed=909)
        self.assertEqual(first, second)
        problem = first["selected_templates"][0]
        self.assertIsInstance(problem["answer_value"], int)
        self.assertNotIn("Ответ:", problem["rendered_problem"])


if __name__ == "__main__":
    unittest.main()
