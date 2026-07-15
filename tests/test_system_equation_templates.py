from __future__ import annotations

import random
import unittest

from problemgen.generation.system_equation_templates import (
    SystemEquationTemplateError,
    generate_system_equation_problem,
    generate_system_equation_problem_from_module,
    load_system_equation_templates,
    solve_system,
    source_system_problem_numbers,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class SystemEquationTemplatesTests(unittest.TestCase):
    def test_every_source_problem_number_is_accounted_for_once(self) -> None:
        numbers: list[int] = []
        for template in load_system_equation_templates():
            numbers.extend(template["source_problem_numbers"])
        self.assertEqual(set(numbers), source_system_problem_numbers())
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(numbers), 8)

    def test_duplicate_source_problems_share_one_template(self) -> None:
        matches = [
            template for template in load_system_equation_templates()
            if set(template["source_problem_numbers"]) == {700, 886}
        ]
        self.assertEqual(len(matches), 1)

    def test_template_ids_are_unique(self) -> None:
        ids = [template["id"] for template in load_system_equation_templates()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_template_generates_200_valid_integer_systems(self) -> None:
        failures: list[str] = []
        source_texts = {
            template["id"]: set(template.get("source_examples", []))
            for template in load_system_equation_templates()
        }
        for template in load_system_equation_templates():
            generated_texts: set[str] = set()
            for seed in range(200):
                try:
                    generated = generate_system_equation_problem(template["id"], seed=seed)
                    p = generated.parameters
                    solved_x, solved_y, determinant = solve_system(
                        p["x_coefficient_1"],
                        p["y_coefficient_1"],
                        p["right_side_1"],
                        p["x_coefficient_2"],
                        p["y_coefficient_2"],
                        p["right_side_2"],
                    )
                    self.assertNotEqual(determinant, 0)
                    self.assertEqual(solved_x.denominator, 1)
                    self.assertEqual(solved_y.denominator, 1)
                    self.assertEqual(int(solved_x), generated.answer["x"])
                    self.assertEqual(int(solved_y), generated.answer["y"])
                    self.assertNotIn("{", generated.problem_text)
                    self.assertNotIn("+ -", generated.problem_text)
                    self.assertNotIn("- -", generated.problem_text)
                    self.assertNotIn("1X", generated.problem_text)
                    self.assertNotIn("-1X", generated.problem_text)
                    self.assertNotIn("1Y", generated.problem_text)
                    self.assertNotIn("-1Y", generated.problem_text)
                    self.assertLessEqual(abs(p["right_side_1"]), 400)
                    self.assertLessEqual(abs(p["right_side_2"]), 400)
                    generated_texts.add(generated.problem_text)
                except Exception as error:  # noqa: BLE001 - тест собирает все хрупкие случаи.
                    failures.append(f"{template['id']}@{seed}: {error}")
            self.assertFalse(generated_texts <= source_texts[template["id"]])
        self.assertEqual(failures, [])

    def test_generation_is_deterministic_for_same_seed(self) -> None:
        first = generate_system_equation_problem("system_equation_001", seed=20260715)
        second = generate_system_equation_problem("system_equation_001", seed=20260715)
        self.assertEqual(first.problem_text, second.problem_text)
        self.assertEqual(first.answer, second.answer)

    def test_different_seeds_normally_generate_different_systems(self) -> None:
        first = generate_system_equation_problem("system_equation_001", seed=1)
        second = generate_system_equation_problem("system_equation_001", seed=2)
        self.assertNotEqual(first.problem_text, second.problem_text)

    def test_module_generation(self) -> None:
        generated = generate_system_equation_problem_from_module("systems_of_equations", rng=random.Random(20260715))
        self.assertEqual(generated.module, "systems_of_equations")
        self.assertTrue(generated.template_id.startswith("system_equation_"))

    def test_invalid_template_and_module_return_clear_errors(self) -> None:
        with self.assertRaises(SystemEquationTemplateError):
            generate_system_equation_problem("no_such_template", seed=1)
        with self.assertRaises(SystemEquationTemplateError):
            generate_system_equation_problem_from_module("geometry", rng=random.Random(1))

    def test_mixed_worksheet_can_contain_all_three_modules(self) -> None:
        worksheet = generate_combined_worksheet_by_modules(
            ["arithmetic", "equations", "systems_of_equations", "arithmetic", "systems_of_equations"],
            seed=20260715,
        )
        self.assertEqual(len(worksheet["selected_templates"]), 5)
        self.assertEqual(
            [problem["module_id"] for problem in worksheet["selected_templates"]],
            ["arithmetic", "equations", "systems_of_equations", "arithmetic", "systems_of_equations"],
        )
        system_answers = [
            problem["answer"]
            for problem in worksheet["selected_templates"]
            if problem["module_id"] == "systems_of_equations"
        ]
        self.assertTrue(all(answer.startswith("X = ") and ", Y = " in answer for answer in system_answers))


if __name__ == "__main__":
    unittest.main()
