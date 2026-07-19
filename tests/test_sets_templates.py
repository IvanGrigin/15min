from __future__ import annotations

import random
import unittest

from problemgen.generation.sets_templates import MODULE_ID, STRATEGIES, generate_sets_problem, load_sets_templates, load_source_accounting, sets_template_metadata, source_problem_numbers
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class SetsTemplatesTests(unittest.TestCase):
    def test_source_accounting_is_complete_and_precise(self) -> None:
        manifest = load_source_accounting()
        records = manifest["records"]
        numbers = [record["source_problem_number"] for record in records]
        self.assertEqual((manifest["original_numbered_entries"], manifest["removed_duplicates"], len(numbers)), (36, 10, 26))
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(set(numbers), source_problem_numbers())
        for record in records:
            if record["status"] == "active_template":
                self.assertIn(record["template_id"], {template["id"] for template in load_sets_templates()})
            else:
                self.assertIn(record["status"], {"excluded_ambiguous_or_non_unique", "excluded_non_integer_answer", "excluded_requires_missing_diagram"})
                self.assertTrue(record.get("reason"))

    def test_schema_strategies_and_exact_answers(self) -> None:
        templates = load_sets_templates()
        self.assertEqual(len(templates), len({template["id"] for template in templates}))
        self.assertEqual({template["generation_strategy"] for template in templates}, set(STRATEGIES))
        for template in templates:
            self.assertEqual(template["module"], MODULE_ID)
            self.assertTrue(template["active"])
            self.assertEqual(template["answer_type"], "integer")
            for seed in range(20):
                generated = generate_sets_problem(template["id"], seed=seed)
                self.assertEqual(generated, generate_sets_problem(template["id"], seed=seed))
                self.assertIsInstance(generated.answer, int)
                self.assertNotIn("{", generated.problem_text)
                self._verify(generated.template_id, generated.parameters, generated.answer)

    def test_module_and_mixed_worksheet_generation(self) -> None:
        self.assertEqual(sets_template_metadata()["stats"]["total_templates"], 8)
        modules = [MODULE_ID, "arithmetic", MODULE_ID, "equations", MODULE_ID]
        worksheet = generate_combined_worksheet_by_modules(modules, seed=123, task_count=5)
        self.assertEqual(worksheet, generate_combined_worksheet_by_modules(modules, seed=123, task_count=5))
        self.assertEqual([task["module_id"] for task in worksheet["selected_templates"]][::2], [MODULE_ID] * 3)
        self.assertTrue(all("Ответ:" not in task["rendered_problem"] for task in worksheet["selected_templates"]))

    def test_rejects_unknown_template(self) -> None:
        with self.assertRaisesRegex(ValueError, "Неизвестный шаблон"):
            generate_sets_problem("sets_unknown", rng=random.Random(1))

    def _verify(self, template_id: str, values: dict[str, int], answer: int) -> None:
        if template_id == "sets_001_two_fields": expected = values["hours_with_two_fields"] * values["field_count"]
        elif template_id == "sets_002_single_elimination": expected = values["participant_count"] - 1
        elif template_id == "sets_003_round_robin":
            dividend = values["participant_count"] * (values["participant_count"] - 1) * values["games_per_pair"]
            self.assertEqual(dividend % 2, 0); expected = dividend // 2
        elif template_id == "sets_004_club_inclusion_exclusion": expected = values["total_people"] - values["music_members"] - values["no_club"] + values["overlap_girls"] - values["boys_in_literature"]
        elif template_id == "sets_005_language_overlap": expected = values["english_members"] + values["french_members"] + values["neither"] - values["total_people"]
        elif template_id == "sets_006_bipartite_handshakes":
            second_count = values["total_people"] - answer
            self.assertEqual(answer * values["first_to_second_degree"], second_count * values["second_to_first_degree"]); expected = answer
        elif template_id == "sets_007_cross_group_score_balance": expected = values["first_group_points"] - values["first_group_size"] * (values["first_group_size"] - 1) - values["cross_game_count"]
        else:
            matches = values["participant_count"] * (values["participant_count"] - 1) // 2
            expected = matches + (values["participant_count"] - 1) + matches
        self.assertEqual(answer, expected)


if __name__ == "__main__": unittest.main()
