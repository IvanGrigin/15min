from __future__ import annotations

import random
import unittest

from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.sequence_templates import (
    SequenceTemplateError,
    character_gender,
    digit_count,
    generate_sequence_problem,
    generate_sequence_problem_from_module,
    load_sequence_templates,
    recurrence_terms,
    recurrence_value,
    solve_digit_count_intervals,
    source_sequence_problem_numbers,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class SequenceTemplatesTests(unittest.TestCase):
    def test_source_accounting_is_complete_and_unique(self) -> None:
        templates = load_sequence_templates()
        numbers = [number for template in templates for number in template["source_problem_numbers"]]
        self.assertEqual(set(numbers), source_sequence_problem_numbers())
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(numbers), 23)
        self.assertEqual(len(templates), 9)
        self.assertEqual(next(item for item in templates if item["id"] == "sequence_001_alternating_steps_sum")["source_problem_numbers"], [28, 1033])
        self.assertEqual(next(item for item in templates if item["id"] == "sequence_002_arithmetic_progression_sum")["source_problem_numbers"], [44, 1051, 1067])

    def test_every_template_generates_200_valid_instances(self) -> None:
        for template in load_sequence_templates():
            texts: set[str] = set()
            for seed in range(200):
                generated = generate_sequence_problem(template["id"], seed=seed)
                texts.add(generated.problem_text)
                self.assertNotIn("{", generated.problem_text)
                self.assertNotIn("}", generated.problem_text)
                self.assertNotIn("+ -", generated.problem_text)
                values = generated.answer.values() if isinstance(generated.answer, dict) else [generated.answer]
                self.assertTrue(all(isinstance(value, int) for value in values))
                params = generated.parameters
                strategy = template["generation_strategy"]
                if strategy == "arithmetic_progression_sum":
                    self.assertEqual(params["terms"][-1], params["start"] + (params["term_count"] - 1) * params["step"])
                    self.assertEqual(generated.answer, sum(params["terms"]))
                if strategy == "alternating_steps_sum":
                    self.assertEqual([b - a for a, b in zip(params["terms"], params["terms"][1:])], [params["step_1"] if i % 2 == 0 else params["step_2"] for i in range(len(params["terms"]) - 1)])
                if strategy in {"product_mod_10", "sum_mod_10"}:
                    operation = params["recurrence_operation"]
                    self.assertEqual(params["shown_terms"], recurrence_terms(params["first_digit"], params["second_digit"], operation, params["shown_term_count"]))
                    self.assertEqual(params["reference_value"], params["shown_terms"][params["reference_position"] - 1])
                    self.assertEqual(generated.answer, recurrence_value(params["first_digit"], params["second_digit"], operation, params["target_position"]))
                if strategy == "cyclic_digit_shift_sum":
                    rotations = params["rotations"]
                    self.assertEqual(len(rotations), len(set(rotations)))
                    self.assertTrue(all(rotations[i] == rotations[0][i:] + rotations[0][:i] for i in range(len(rotations))))
                if strategy.startswith("digit_count"):
                    self.assertEqual(params["total_digit_count"], digit_count(params["first_number"], params["count_of_numbers"]))
                    self.assertEqual(params["number_of_solutions"], 1)
                    self.assertEqual(solve_digit_count_intervals(params["count_of_numbers"], params["total_digit_count"]), [params["first_number"]])
            self.assertGreater(len(texts), 1)

    def test_cycle_detection_matches_direct_iteration(self) -> None:
        for operation in ("multiplication_mod_10", "addition_mod_10"):
            for first in range(10):
                for second in range(10):
                    for position in range(1, 101):
                        self.assertEqual(recurrence_value(first, second, operation, position), recurrence_terms(first, second, operation, position)[-1])

    def test_named_templates_use_one_approved_universe_and_grammar(self) -> None:
        approved = load_approved_characters()
        for template_id in ("sequence_008_digit_count_find_first", "sequence_009_digit_count_find_last"):
            for seed in range(200):
                generated = generate_sequence_problem(template_id, seed=seed)
                self.assertIn(generated.universe, approved)
                self.assertEqual(len(generated.characters or []), 1)
                character = next(item for item in approved[generated.universe or ""] if item.name == generated.characters[0])
                self.assertIn(generated.characters[0][:1].upper() + generated.characters[0][1:], generated.problem_text)
                self.assertIn("заметила" if character_gender(character) == "feminine" else "заметил", generated.problem_text)
        unnamed = generate_sequence_problem("sequence_001_alternating_steps_sum", seed=3)
        self.assertIsNone(unnamed.universe)
        self.assertIsNone(unnamed.characters)

    def test_module_and_mixed_worksheet_are_deterministic(self) -> None:
        first = generate_sequence_problem_from_module("sequences_progressions_and_sums", rng=random.Random(17))
        second = generate_sequence_problem_from_module("sequences_progressions_and_sums", rng=random.Random(17))
        self.assertEqual(first, second)
        modules = ["arithmetic", "equations", "systems_of_equations", "comparison_of_numbers_and_expressions", "sequences_progressions_and_sums"]
        worksheet = generate_combined_worksheet_by_modules(modules, seed=20260715)
        self.assertEqual(worksheet, generate_combined_worksheet_by_modules(modules, seed=20260715))
        self.assertEqual([item["module_id"] for item in worksheet["selected_templates"]], modules)

    def test_invalid_ids_raise_clear_errors(self) -> None:
        with self.assertRaises(SequenceTemplateError):
            generate_sequence_problem("not-a-template", seed=1)
        with self.assertRaises(SequenceTemplateError):
            generate_sequence_problem_from_module("arithmetic", rng=random.Random(1))


if __name__ == "__main__":
    unittest.main()
