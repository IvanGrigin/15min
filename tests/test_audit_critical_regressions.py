"""Регрессии по критическим seed из аудита 1 000 сгенерированных задач."""
from __future__ import annotations

from fractions import Fraction
from math import gcd
import unittest

from problemgen.generation.clock_templates import generate_clock_problem
from problemgen.generation.cube_templates import generate_cube_problem
from problemgen.generation.motion_templates import generate_motion_problem
from problemgen.generation.quantity_templates import generate_quantity_problem
from problemgen.generation.sets_templates import generate_sets_problem


class CriticalAuditRegressionTests(unittest.TestCase):
    """Проверки используют формулы, независимые от рендерящих стратегий."""

    def test_train_old_audit_seeds_answer_in_seconds(self):
        for seed in (20260724, 20260732, 20260757, 20260823):
            problem = generate_motion_problem("motion_004_train_overlap", seed=seed)
            lengths = sum(problem.parameters["lengths"])
            speeds = sum(problem.parameters["speeds"])
            expected = Fraction(lengths * 3600, speeds * 1000)
            self.assertEqual(expected.denominator, 1)
            self.assertEqual(problem.answer, expected.numerator)
            self.assertIn(" м и ", problem.problem_text)

    def test_cube_formula_regressions(self):
        for seed in (20260883, 20261020, 20261420):
            painted = generate_cube_problem("cube_002_painted_cubes", seed=seed)
            a, b, c = (painted.parameters[key] for key in ("a", "b", "c"))
            self.assertEqual(painted.answer, 4 * (a - 2) + 4 * (b - 2) + 4 * (c - 2))
            water = generate_cube_problem("cube_003_water_depth", seed=seed)
            self.assertEqual(water.answer, water.parameters["volume_l"] // (water.parameters["width_m"] * water.parameters["length_m"]))
            packing = generate_cube_problem("cube_004_packing", seed=seed)
            p = packing.parameters
            self.assertEqual(p["cube_side"] % p["block_x"], 0)
            self.assertEqual(p["cube_side"] % p["block_y"], 0)
            self.assertEqual(p["cube_side"] % p["block_z"], 0)
            visible = generate_cube_problem("cube_005_visible_faces_sum", seed=seed)
            self.assertEqual(visible.answer, 6 * visible.parameters["side"] ** 2)

    def test_conservation_and_schedule_regressions(self):
        watermelon = generate_quantity_problem("quantity_004_watermelon", seed=20261020)
        self.assertEqual(watermelon.answer * 2, watermelon.parameters["initial_mass"])
        bridge = generate_quantity_problem("quantity_003_bridge", seed=20261248)
        self.assertEqual(bridge.answer * (bridge.parameters["denominator"] - 2), bridge.parameters["river_width"] * bridge.parameters["denominator"])
        fields = generate_sets_problem("sets_001_two_fields", seed=20261028)
        self.assertEqual(fields.answer, 6 * fields.parameters["game_hours"])
        self.assertEqual(fields.parameters["hours_with_two_fields"], 3 * fields.parameters["game_hours"])

    def test_clock_old_audit_seed_uses_relative_drift(self):
        problem = generate_clock_problem("clock_004_drifting_watches", seed=20260742)
        p = problem.parameters
        relative = p["fast_minutes_per_day"] + p["slow_minutes_per_day"]
        self.assertEqual(problem.answer, 1440 // gcd(relative, 1440))
        self.assertEqual(p["first_reading"], p["second_reading"])


if __name__ == "__main__":
    unittest.main()
