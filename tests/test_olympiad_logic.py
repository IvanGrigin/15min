from __future__ import annotations

import random
import unittest

from problemgen.app import generate_problem_bundle
from problemgen.core.story_worlds import sample_story_context
from problemgen.domains.olympiad_logic import templates
from problemgen.domains.olympiad_logic.validators import (
    validate_birds_count,
    validate_digit_erasing,
    validate_shared_payment_debt,
    validate_three_numbers_same_suffix,
)


class OlympiadLogicTemplatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rng = random.Random(123)
        self.story_context = sample_story_context(rng=self.rng, world_key="smeshariki")

    def test_digit_erasing_template_generates_answer_and_story(self) -> None:
        problem = templates.generate_digit_erasing(
            rng=self.rng,
            index=1,
            difficulty_level="medium",
            story_context=self.story_context,
        )
        self.assertTrue(problem.answer_values)
        self.assertEqual(problem.story["world_key"], "smeshariki")
        self.assertTrue(
            validate_digit_erasing(
                start_value=problem.answer_values[0],
                first_multiplier=problem.variables["first_multiplier"],
                second_multiplier=problem.variables["second_multiplier"],
                final_value=problem.variables["final_value"],
            )
        )

    def test_birds_count_template_generates_answer_and_story(self) -> None:
        problem = templates.generate_birds_count(
            rng=self.rng,
            index=1,
            difficulty_level="medium",
            story_context=self.story_context,
        )
        self.assertTrue(problem.answer_values)
        self.assertEqual(problem.story["world_key"], "smeshariki")
        self.assertTrue(
            validate_birds_count(
                initial_count=problem.answer_values[0],
                total_after_expansion=problem.variables["total_after_expansion"],
            )
        )

    def test_three_numbers_template_generates_valid_numbers(self) -> None:
        problem = templates.generate_three_numbers_same_suffix(
            rng=self.rng,
            index=1,
            difficulty_level="medium",
            story_context=self.story_context,
        )
        self.assertEqual(problem.story["world_key"], "smeshariki")
        self.assertTrue(
            validate_three_numbers_same_suffix(
                numbers=problem.answer_values,
                target_sum=problem.variables["target_sum"],
            )
        )

    def test_shared_payment_template_generates_valid_answer(self) -> None:
        problem = templates.generate_shared_payment_debt(
            rng=self.rng,
            index=1,
            difficulty_level="medium",
            story_context=self.story_context,
        )
        self.assertEqual(problem.story["world_key"], "smeshariki")
        self.assertTrue(
            validate_shared_payment_debt(
                total_cost=problem.variables["total_cost"],
                loan_amount=problem.variables["loan_amount"],
                second_paid=problem.variables["second_paid"],
                expected_transfer=problem.answer_values[0],
            )
        )

    def test_bundle_with_story_world_uses_requested_world(self) -> None:
        bundle = generate_problem_bundle(
            domain_code="olympiad_logic",
            count=3,
            template_name="digit_erasing",
            difficulty_level="easy",
            story_theme="any",
            story_world="smeshariki",
            seed_mode="fixed",
            seed=7,
            output_path=None,
            options={},
        )
        self.assertEqual(bundle["requested_story_world"], "smeshariki")
        for problem in bundle["problems"]:
            self.assertEqual(problem["story"]["world_key"], "smeshariki")


if __name__ == "__main__":
    unittest.main()
