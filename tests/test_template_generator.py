from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from problemgen.catalog.problem_templates import find_templates, list_modules, load_template_catalog
from problemgen.generation.template_generator import evaluate_formula, generate_problem_from_template
from problemgen.worksheet.service import validate_items
from problemgen.worksheet.service import generate_worksheet_artifacts


class TemplateGeneratorTests(unittest.TestCase):
    def test_catalog_has_unique_valid_template_ids(self) -> None:
        templates = load_template_catalog()
        self.assertGreaterEqual(len(templates), 8)
        self.assertEqual(len({template["template_id"] for template in templates}), len(templates))

    def test_every_template_can_generate_an_integer_answer(self) -> None:
        for index, template in enumerate(load_template_catalog(), start=1):
            problem = generate_problem_from_template(
                template["module"], template["supported_difficulties"][0], rng=random.Random(index)
            )
            self.assertTrue(problem.problem_text)
            self.assertNotIn("{", problem.problem_text)
            self.assertIsInstance(problem.answer, int)

    def test_module_filter_returns_matching_static_templates(self) -> None:
        templates = find_templates("joint_work", 4)
        self.assertTrue(templates)
        self.assertTrue(all(template["module"] == "joint_work" for template in templates))

    def test_formula_evaluator_rejects_function_calls(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("open('bad')", {})

    def test_every_visible_module_accepts_a_valid_item(self) -> None:
        modules = list_modules()
        items = [
            {"module": module["id"], "difficulty": module["available_difficulties"][0]}
            for module in (modules * 5)[:5]
        ]
        self.assertEqual(validate_items(items), items)

    def test_items_require_exactly_five_entries(self) -> None:
        with self.assertRaises(ValueError):
            validate_items([{"module": "ages", "difficulty": 3}])

    def test_items_reject_module_without_matching_difficulty(self) -> None:
        items = [{"module": "round_robin", "difficulty": 1} for _ in range(5)]
        with self.assertRaises(ValueError):
            validate_items(items)

    @patch("problemgen.worksheet.service.render_worksheet")
    def test_worksheet_has_exactly_five_template_problems(self, render_worksheet: object) -> None:
        items = [
            {"module": "joint_work", "difficulty": 4},
            {"module": "ages", "difficulty": 3},
            {"module": "heads_and_legs", "difficulty": 4},
            {"module": "ratios", "difficulty": 3},
            {"module": "movement", "difficulty": 4},
        ]
        with tempfile.TemporaryDirectory() as directory:
            artifact = generate_worksheet_artifacts(items=items, output_dir=directory, seed=42)
            self.assertEqual(len(artifact.problems), 5)
            self.assertEqual(len(artifact.items), 5)
            self.assertTrue(Path(artifact.student_json_path).exists())
            self.assertTrue(Path(artifact.answers_json_path).exists())
            self.assertEqual(render_worksheet.call_count, 1)


if __name__ == "__main__":
    unittest.main()
