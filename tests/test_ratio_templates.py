from __future__ import annotations

import json
import random
import unittest
from datetime import date

from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.ratio_templates import (
    DEFAULT_ACCOUNTING_PATH,
    RatioTemplateError,
    STRATEGIES,
    generate_ratio_problem,
    generate_ratio_problem_from_module,
    load_ratio_templates,
    load_source_accounting,
    solve_distinct_positive_parts,
    solve_repeated_halving,
    source_ratio_problem_numbers,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class RatioTemplateTests(unittest.TestCase):
    def test_source_accounting_is_exact(self) -> None:
        manifest = load_source_accounting()
        records = manifest["records"]
        numbers = [record["source_problem_number"] for record in records]
        self.assertEqual(manifest["original_numbered_entries"], 35)
        self.assertEqual(manifest["removed_duplicates"], 9)
        self.assertEqual(len(numbers), 26)
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(set(numbers), source_ratio_problem_numbers())
        for record in records:
            if record["status"] != "active_template":
                self.assertGreater(len(record["reason"]), 20)

    def test_catalog_schema_and_registration(self) -> None:
        templates = load_ratio_templates()
        self.assertEqual(len({template["id"] for template in templates}), len(templates))
        for template in templates:
            self.assertEqual(template["answer_type"], "integer")
            self.assertTrue(template["active"])
            self.assertIn(template["generation_strategy"], STRATEGIES)
            self.assertNotRegex(template["render_template"], r"\{number_\d+\}")

    def test_manifest_active_records_match_runtime_templates(self) -> None:
        records = load_source_accounting()["records"]
        active = {record["source_problem_number"]: record["template_id"] for record in records if record["status"] == "active_template"}
        expected = {number: template["id"] for template in load_ratio_templates() for number in template["source_problem_numbers"]}
        self.assertEqual(active, expected)

    def test_independent_solvers_cover_edges_and_invalid_values(self) -> None:
        for total in (1, 3, 6, 7, 28, 1000):
            brute = max(count for count in range(1, total + 1) if count * (count + 1) // 2 <= total)
            self.assertEqual(solve_distinct_positive_parts(total), brute)
        self.assertEqual(solve_repeated_halving(655, 10), 7)
        with self.assertRaises(RatioTemplateError):
            solve_distinct_positive_parts(0)
        with self.assertRaises(RatioTemplateError):
            solve_repeated_halving(10, 0)

    def test_every_strategy_has_twenty_exact_reproducible_samples(self) -> None:
        for template in load_ratio_templates():
            for seed in range(20):
                generated = generate_ratio_problem(template["id"], seed=seed)
                self.assertIsInstance(generated.answer, int)
                self.assertNotIn("{", generated.problem_text)
                self.assertEqual(generated, generate_ratio_problem(template["id"], seed=seed))

    def test_strategy_specific_exact_invariants(self) -> None:
        for template in load_ratio_templates():
            for seed in range(20):
                generated = generate_ratio_problem(template["id"], seed=seed)
                p = generated.parameters
                strategy = template["generation_strategy"]
                if strategy == "distinct_positive_parts":
                    self.assertEqual(generated.answer, solve_distinct_positive_parts(p["total_items"]))
                elif strategy == "three_box_differences":
                    self.assertEqual(2 * generated.answer, p["second_shortfall"] - p["first_shortfall"])
                elif strategy == "fraction_percentage":
                    self.assertEqual(generated.answer * p["denominator"], 100 * p["numerator"])
                elif strategy == "repeated_halving_bound":
                    self.assertEqual(generated.answer, solve_repeated_halving(p["initial_count"], p["threshold"]))
                elif strategy == "same_weekday_birthday":
                    start = date(p["year"], p["month"], p["day"])
                    finish = date(p["year"] + generated.answer, p["month"], p["day"])
                    self.assertEqual(start.weekday(), finish.weekday())
                elif strategy == "box_conservation":
                    self.assertEqual(generated.answer + p["final_first"] + p["final_second"], sum(p["initial_counts"]))

    def test_named_strategies_use_one_approved_universe_and_distinct_roles(self) -> None:
        approved = {universe: {character.name for character in chars} for universe, chars in load_approved_characters().items()}
        named = [template for template in load_ratio_templates() if template["uses_characters"]]
        for template in named:
            for seed in range(20):
                generated = generate_ratio_problem(template["id"], seed=seed)
                self.assertIn(generated.universe, approved)
                self.assertEqual(len(generated.characters), template["required_character_count"])
                self.assertEqual(len(generated.characters), len(set(generated.characters)))
                self.assertTrue(set(generated.characters) <= approved[generated.universe])
                # Имена остаются целыми и в именительном падеже; согласование — безопасное множественное.
                self.assertTrue(all(name in generated.problem_text for name in generated.characters))
                self.assertTrue(all(name not in template["render_template"] for name in ("Света", "Маша", "Оля", "Петя", "Марк", "Вася")))

    def test_runtime_selection_never_uses_exclusions(self) -> None:
        excluded = {record["source_problem_number"] for record in load_source_accounting()["records"] if record["status"] != "active_template"}
        for seed in range(200):
            generated = generate_ratio_problem_from_module("ratios_fractions_proportions_and_percentages", rng=random.Random(seed))
            self.assertTrue(excluded.isdisjoint(generated.source_problem_numbers))

    def test_site_mixed_worksheet_and_answer_separation(self) -> None:
        modules = ["ratios_fractions_proportions_and_percentages", "arithmetic", "ratios_fractions_proportions_and_percentages", "equations", "ratios_fractions_proportions_and_percentages"]
        first = generate_combined_worksheet_by_modules(modules, seed=239)
        self.assertEqual(first, generate_combined_worksheet_by_modules(modules, seed=239))
        for task in first["selected_templates"]:
            self.assertNotIn(str(task["answer"]), task["rendered_problem"][-20:])


if __name__ == "__main__":
    unittest.main()
