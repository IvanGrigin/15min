import json
import random
import unittest
from pathlib import Path

from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.logic_templates import (
    MODULE_ID,
    PATH,
    circular_liar_count,
    generate_logic_problem,
    generate_logic_problem_from_module,
    load_logic_templates,
    load_source_accounting,
    only_one_truthful_count,
    solve_wrong_product,
    source_problem_numbers,
)


class LogicTemplatesTest(unittest.TestCase):
    def test_source_accounting_is_one_to_one(self) -> None:
        records = load_source_accounting()["records"]
        numbers = [record["source_problem_number"] for record in records]
        self.assertEqual(len(numbers), 37)
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(set(numbers), source_problem_numbers())
        self.assertEqual(set(numbers) & {65, 84, 427}, set())
        active = {number: template["id"] for template in load_logic_templates() for number in template["source_problem_numbers"]}
        for record in records:
            if record["status"] == "active_template":
                self.assertEqual(active[record["source_problem_number"]], record["template_id"])
            else:
                self.assertTrue(record["reason"])

    def test_json_schema_and_registered_strategies(self) -> None:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
        templates = load_logic_templates()
        self.assertEqual(payload["module_id"], MODULE_ID)
        self.assertEqual(len({template["id"] for template in templates}), len(templates))
        for template in templates:
            self.assertTrue(template["active"])
            self.assertEqual(template["answer_type"], "integer")
            self.assertNotIn("{number_", template["render_template"])

    def test_exact_solvers_and_invalid_inputs(self) -> None:
        self.assertEqual(solve_wrong_product(23, (11, 13, 17), (253, 299, 390)), 391)
        with self.assertRaises(ValueError):
            solve_wrong_product(23, (11, 13, 17), (253, 299, 391))
        self.assertEqual(circular_liar_count(10, 4), 8)
        self.assertEqual(only_one_truthful_count(1000), 1)

    def test_seeded_instances_are_exact_and_reproducible(self) -> None:
        for template in load_logic_templates():
            for seed in range(20):
                generated = generate_logic_problem(template["id"], seed=seed)
                self.assertEqual(generated, generate_logic_problem(template["id"], seed=seed))
                self.assertIsInstance(generated.answer, int)
                self.assertNotIn("{", generated.problem_text)
                if template["generation_strategy"] == "one_wrong_product":
                    self.assertEqual(generated.answer, solve_wrong_product(generated.parameters["base_value"], tuple(generated.parameters["multipliers"]), tuple(generated.parameters["reported_products"])))
                elif template["generation_strategy"] == "circular_liars":
                    self.assertEqual(generated.answer, circular_liar_count(generated.parameters["participant_count"], generated.parameters["following_count"]))
                else:
                    self.assertEqual(generated.answer, only_one_truthful_count(generated.parameters["population"]))

    def test_named_family_uses_one_approved_universe_and_distinct_names(self) -> None:
        approved = {universe: {character.name for character in characters} for universe, characters in load_approved_characters().items()}
        for seed in range(20):
            generated = generate_logic_problem("logic_001_one_wrong_product", seed=seed)
            self.assertIn(generated.universe, approved)
            self.assertTrue(set(generated.characters or []) <= approved[generated.universe])
            self.assertEqual(len(generated.characters or []), len(set(generated.characters or [])))

    def test_wrong_product_has_complete_role_neutral_context(self) -> None:
        generated = generate_logic_problem("logic_001_one_wrong_product", seed=4)

        self.assertIn("Учитель дал трём участникам примеры", generated.problem_text)
        self.assertIn("ошибочной карточке", generated.problem_text)
        self.assertNotIn("ошибившегося ученика", generated.problem_text)

    def test_module_random_selection_never_selects_excluded_records(self) -> None:
        active_ids = {template["id"] for template in load_logic_templates()}
        for seed in range(100):
            self.assertIn(generate_logic_problem_from_module(MODULE_ID, rng=random.Random(seed)).template_id, active_ids)


if __name__ == "__main__":
    unittest.main()
