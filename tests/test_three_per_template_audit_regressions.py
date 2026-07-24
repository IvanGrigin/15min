"""Регрессии для критических seed из аудита three-per-active-template."""
from __future__ import annotations

from fractions import Fraction
import unittest

from problemgen.generation.digits_templates import generate_digits_problem
from problemgen.generation.motion_templates import generate_motion_problem
from problemgen.generation.parity_templates import (
    generate_parity_problem,
    has_equal_adjacent_parity,
)
from problemgen.generation.time_zone_templates import local_to_absolute


class ThreePerTemplateAuditRegressions(unittest.TestCase):
    def test_math_001_alternating_displacement_old_seeds(self) -> None:
        expected = {41032000: 27, 41032001: 54, 41032002: 3}
        for seed, answer in expected.items():
            problem = generate_motion_problem("motion_001_alternating_displacement", seed=seed)
            p = problem.parameters
            direct = abs(sum((1 if i % 2 else -1) * i * p["step_m"] for i in range(1, p["minutes"] + 1)))
            self.assertEqual(problem.answer, answer, f"MATH-001 seed={seed}")
            self.assertEqual(problem.answer, direct, f"MATH-001 seed={seed}")
            self.assertIn(" м", problem.problem_text)

    def test_math_002_next_day_elapsed_uses_absolute_time(self) -> None:
        # These are the audited rendered endpoints, independent from the
        # random strategy: next-day arrival must not be reduced modulo 24 h.
        cases = [
            (6 * 60 + 33, -120, 23 * 60 + 23, 0, 2330),
            (13 * 60 + 8, 0, 21 * 60 + 19, 120, 1811),
        ]
        for start, origin_offset, arrival, destination_offset, expected in cases:
            elapsed = local_to_absolute(24 * 60 + arrival, destination_offset) - local_to_absolute(start, origin_offset)
            self.assertEqual(elapsed, expected, "MATH-002 absolute next-day subtraction")

    def test_math_003_rendered_digit_predicate(self) -> None:
        problem = generate_parity_problem("parity_001_adjacent_digit_classification_sum", seed=41029202)
        values = problem.parameters["candidate_numbers"]
        self.assertEqual(problem.answer, sum(value for value in values if has_equal_adjacent_parity(value)))
        self.assertIn("хотя бы две соседние цифры одинаковой чётности", problem.problem_text)
        audited = (6836408, 1412620, 6738341, 7307568, 4721481)
        self.assertEqual(sum(value for value in audited if has_equal_adjacent_parity(value)), 27016418)

    def test_math_004_fly_distance_is_fraction_exact(self) -> None:
        problem = generate_motion_problem("motion_006_fly_distance", seed=41032501)
        distance = problem.parameters["distance"]
        first, second = problem.parameters["speeds"]
        expected = Fraction(distance * problem.parameters["fly_speed"], first + second)
        self.assertEqual(expected.denominator, 1)
        self.assertEqual(problem.answer, expected.numerator)
        self.assertEqual(Fraction(40 * 180, 8 + 10), 400)

    def test_math_005_parity_without_forbidden_digit_uses_rendered_interval(self) -> None:
        for seed in (41024500, 41024501, 41024502):
            problem = generate_digits_problem("digits_006_parity_excludes", seed=seed)
            p = problem.parameters
            expected = sum(
                number % 2 == p["parity"] and str(p["digit"]) not in str(number)
                for number in range(p["lower"], p["upper"] + 1)
            )
            self.assertEqual(problem.answer, expected, f"MATH-005 seed={seed}")


if __name__ == "__main__":
    unittest.main()
