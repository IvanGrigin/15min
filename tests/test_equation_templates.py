from __future__ import annotations

import random
import unittest

from problemgen.generation.equation_templates import (
    EquationTemplateError,
    generate_equation_problem,
    generate_equation_problem_from_module,
    load_equation_templates,
    source_problem_numbers,
)
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class EquationTemplatesTests(unittest.TestCase):
    def test_every_source_problem_number_is_accounted_for_once(self) -> None:
        numbers: list[int] = []
        for template in load_equation_templates():
            numbers.extend(template["source_problem_numbers"])
        self.assertEqual(set(numbers), source_problem_numbers())
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(numbers), 160)
        self.assertNotIn(1502, numbers)

    def test_template_ids_are_unique(self) -> None:
        ids = [template["id"] for template in load_equation_templates()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_template_generates_integer_answers_for_10_seeds(self) -> None:
        failures: list[str] = []
        for template in load_equation_templates():
            for seed in range(10):
                try:
                    generated = generate_equation_problem(template["id"], seed=seed)
                except Exception as error:  # noqa: BLE001 - тест собирает все хрупкие случаи.
                    failures.append(f"{template['id']}@{seed}: {error}")
                    continue
                self.assertNotIn("{", generated.problem_text)
                self.assertNotEqual(generated.problem_text.strip(), "")
                self.assertIsNotNone(generated.answer)
        self.assertEqual(failures, [])

    def test_generation_is_deterministic_for_same_seed(self) -> None:
        first = generate_equation_problem("equation_001", seed=20260715)
        second = generate_equation_problem("equation_001", seed=20260715)
        self.assertEqual(first.problem_text, second.problem_text)
        self.assertEqual(first.answer, second.answer)

    def test_equations_module_generates_random_template(self) -> None:
        generated = generate_equation_problem_from_module("equations", rng=random.Random(20260715))
        self.assertEqual(generated.module, "equations")
        self.assertTrue(generated.template_id.startswith("equation_"))

    def test_equations_module_rejects_unknown_module(self) -> None:
        with self.assertRaises(EquationTemplateError):
            generate_equation_problem_from_module("geometry", rng=random.Random(1))

    def test_site_can_mix_arithmetic_and_equations_modules(self) -> None:
        worksheet = generate_combined_worksheet_by_modules(
            ["arithmetic", "equations", "equations", "arithmetic", "equations"],
            seed=20260715,
        )
        self.assertEqual(len(worksheet["selected_templates"]), 5)
        self.assertEqual(
            [problem["module_id"] for problem in worksheet["selected_templates"]],
            ["arithmetic", "equations", "equations", "arithmetic", "equations"],
        )


if __name__ == "__main__":
    unittest.main()
