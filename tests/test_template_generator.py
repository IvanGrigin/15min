from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from problemgen.catalog.problem_templates import find_templates, list_modules, load_template_catalog
from problemgen.generation.template_generator import (
    evaluate_formula,
    generate_problem_from_template,
    registered_strategies,
)
from problemgen.worksheet.service import validate_items
from problemgen.worksheet.service import generate_worksheet_artifacts


class TemplateGeneratorTests(unittest.TestCase):
    def test_catalog_has_unique_valid_template_ids(self) -> None:
        templates = load_template_catalog()
        self.assertGreaterEqual(len(templates), 8)
        self.assertEqual(len({template["template_id"] for template in templates}), len(templates))

    def test_every_template_can_generate_an_answer(self) -> None:
        expected = {"number": int, "multi": list, "text": str}
        for index, template in enumerate(load_template_catalog(), start=1):
            problem = generate_problem_from_template(
                template["module"], template["supported_difficulties"][0], rng=random.Random(index)
            )
            self.assertTrue(problem.problem_text)
            self.assertNotIn("{", problem.problem_text)
            self.assertIsInstance(problem.answer, expected[template.get("answer_type", "number")])

    def test_every_template_strategy_is_registered(self) -> None:
        available = registered_strategies()
        for template in load_template_catalog():
            self.assertIn(
                template["number_strategy"], available,
                msg=f"У шаблона {template['template_id']} нет зарегистрированной стратегии чисел.",
            )

    def test_no_template_is_fragile_across_seeds(self) -> None:
        # Страж против рассинхрона стратегии и constraints: каждый шаблон должен
        # генерироваться без ошибок на нескольких сложностях и сидах.
        failures = []
        for template in load_template_catalog():
            diffs = template.get("supported_difficulties", [template["difficulty"]])
            for difficulty in {diffs[0], diffs[len(diffs) // 2], diffs[-1]}:
                for seed in range(6):
                    try:
                        generate_problem_from_template(
                            template["module"], difficulty, rng=random.Random(seed * 131 + difficulty)
                        )
                    except Exception as error:  # noqa: BLE001 — фиксируем любой сбой генерации
                        failures.append(f"{template['template_id']}@d{difficulty}: {error}")
        self.assertEqual(failures, [], msg=f"Хрупкие шаблоны: {failures[:5]}")

    def test_ratio_split_is_never_degenerate(self) -> None:
        for seed in range(50):
            problem = generate_problem_from_template("ratios", 5, rng=random.Random(seed))
            self.assertGreater(problem.variables["ratio_a"], problem.variables["ratio_b"])

    def test_module_filter_returns_matching_static_templates(self) -> None:
        templates = find_templates("joint_work", 4)
        self.assertTrue(templates)
        self.assertTrue(all(template["module"] == "joint_work" for template in templates))

    def test_formula_evaluator_rejects_function_calls(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("open('bad')", {})

    def test_formula_evaluator_rejects_non_whitelisted_function(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("eval('1')", {})

    def test_formula_evaluator_supports_extended_operators(self) -> None:
        self.assertEqual(evaluate_formula("a // b", {"a": 17, "b": 5}), 3)
        self.assertEqual(evaluate_formula("a % b", {"a": 17, "b": 5}), 2)
        self.assertEqual(evaluate_formula("a ** b", {"a": 2, "b": 10}), 1024)

    def test_formula_evaluator_caps_exponent(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("2 ** n", {"n": 1000})

    def test_formula_evaluator_supports_whitelisted_functions(self) -> None:
        self.assertEqual(evaluate_formula("gcd(a, b)", {"a": 24, "b": 36}), 12)
        self.assertEqual(evaluate_formula("lcm(a, b)", {"a": 4, "b": 6}), 12)
        self.assertEqual(evaluate_formula("comb(n, k)", {"n": 5, "k": 2}), 10)
        self.assertEqual(evaluate_formula("count_digit(7, 1, 100)", {}), 20)
        self.assertEqual(evaluate_formula("digit_sum(n)", {"n": 12345}), 15)
        self.assertEqual(evaluate_formula("first_digit(987654)", {}), 9)
        self.assertEqual(evaluate_formula("inverse_truncated_twice(20, 5, 137)", {}), 137)

    def test_formula_evaluator_supports_multi_and_text_answers(self) -> None:
        self.assertEqual(evaluate_formula("[max(a, b), abs(a - b)]", {"a": 9, "b": 4}), [9, 5])
        self.assertEqual(evaluate_formula("weekday_after(0, 8)", {}), "вторник")

    def test_extended_engine_templates_generate_expected_answer_types(self) -> None:
        cases = {"digit_count": int, "gcd": int, "weekday": str, "product_compare": list}
        for module, kind in cases.items():
            problem = generate_problem_from_template(module, 4, rng=random.Random(11))
            self.assertIsInstance(problem.answer, kind)
            self.assertNotIn("{", problem.problem_text)

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
