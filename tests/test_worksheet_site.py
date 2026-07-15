from __future__ import annotations

import copy
from pathlib import Path
import random
import unittest

from problemgen.web.worksheet_site import (
    RECOVERED_ARCHIVE_MODULE_ID,
    _combined_template_metadata,
    generate_combined_worksheet_by_modules,
    generate_random_worksheet,
    render_site_page,
)
from problemgen.source_index.answer_definition_cleanup import evaluate_formula
from problemgen.worksheet.all_tasks_site import (
    catalog_metadata,
    filter_eligible_templates,
    generate_problem_instance,
    has_only_number_placeholders,
    number_placeholder_names,
    recovered_templates,
    recovery_stats,
    render_template,
    verify_literal_integrity,
)


class WorksheetSiteTests(unittest.TestCase):
    def test_site_renders_configurable_builder_and_print_answer_strip(self) -> None:
        page = render_site_page()

        self.assertIn('id="task-count"', page)
        self.assertIn('id="quick-generate-button"', page)
        self.assertIn('id="selector-grid"', page)
        self.assertIn('id="print-answers-list"', page)
        self.assertIn("Отрезать по пунктиру", page)
        self.assertIn("Генератор математических задач", page)
        self.assertIn("Сгенерировать вариант", page)
        self.assertIn("Показать ответы", page)

    def test_random_generation_respects_requested_count_and_uses_verified_modules(self) -> None:
        worksheet = generate_random_worksheet(7, seed=20260715)

        self.assertEqual(len(worksheet["selected_templates"]), 7)
        self.assertEqual(worksheet["mode"], "random_verified_modules")
        self.assertTrue(all(problem["answer_value"] is not None for problem in worksheet["selected_templates"]))

    def test_archive_module_is_available_but_never_claims_an_unverified_answer(self) -> None:
        worksheet = generate_combined_worksheet_by_modules(["all_tasks_archive"], seed=1)
        problem = worksheet["selected_templates"][0]

        self.assertEqual(problem["answer_value"], None)
        self.assertIn("ещё не восстановлен", problem["answer"])

    def test_recovered_archive_module_returns_a_verified_formula_answer(self) -> None:
        worksheet = generate_combined_worksheet_by_modules([RECOVERED_ARCHIVE_MODULE_ID], seed=1)
        problem = worksheet["selected_templates"][0]

        self.assertIsInstance(problem["answer_value"], int)
        self.assertEqual(problem["answer_status"], "verified")

    def test_answer_recovery_formulas_match_their_source_values(self) -> None:
        expected_answers = {
            "linear_equation_chain_00041": 1283,
            "linear_equation_chain_00042": 1218,
            "linear_equation_chain_00108": 67200,
            "linear_equation_chain_00121": 31247,
            "linear_equation_chain_00134": 31247,
            "divisibility_interval_00559": 313,
            "divisibility_interval_00576": 313,
            "arithmetic_word_model_01031": 91,
            "motion_piecewise_00863": 8,
            "motion_piecewise_00865": 12,
            "divisibility_interval_00560": 29,
            "heads_and_legs_00247": 14,
            "heads_and_legs_00248": 1400,
        }

        templates = {template["template_id"]: template for template in recovered_templates()}

        self.assertEqual(set(templates), set(expected_answers))
        for template_id, expected_answer in expected_answers.items():
            self.assertEqual(
                evaluate_formula(templates[template_id]["answer_formula"], templates[template_id]),
                expected_answer,
            )

    def test_recovered_formulas_generate_integer_answers_with_new_values(self) -> None:
        for template in recovered_templates():
            for seed in range(25):
                generated = generate_problem_instance(template, random.Random(seed))
                self.assertIsInstance(generated["answer"], int)
                self.assertNotIn("{number_", generated["rendered_problem"])

    def test_metadata_distinguishes_verified_and_archive_catalogs(self) -> None:
        metadata = _combined_template_metadata()

        self.assertEqual(metadata["stats"]["verified_answer_templates"], 215)
        self.assertEqual(metadata["stats"]["archive_templates"], 1088)
        self.assertEqual(metadata["stats"]["catalog_templates"], 1303)
        self.assertEqual(metadata["stats"]["recovered_archive_templates"], 13)
        self.assertEqual(metadata["stats"]["unverified_archive_templates"], 1075)

    def test_recovery_stats_keep_the_archive_partitioned(self) -> None:
        self.assertEqual(recovery_stats(), {"recovered_templates": 13, "unverified_templates": 1075})

    def test_current_catalog_allows_restored_templates_as_fallback(self) -> None:
        result = filter_eligible_templates()

        self.assertEqual(result.stats["total_templates"], 1088)
        self.assertEqual(result.stats["eligible_templates"], 1088)
        self.assertEqual(result.stats["excluded_templates"], 0)
        self.assertEqual(result.stats["selectable_without_answer_formula"], 1088)

    def test_template_api_returns_all_selectable_templates(self) -> None:
        metadata = catalog_metadata()

        self.assertEqual(len(metadata["templates"]), 1088)

    def test_frontend_does_not_limit_template_dropdown_to_first_matches(self) -> None:
        script = (Path(__file__).resolve().parents[1] / "frontend" / "worksheet_site.js").read_text(encoding="utf-8")

        self.assertNotIn(".slice(0, 80)", script)

    def test_placeholder_names_sort_numerically(self) -> None:
        text = "{number_10} + {number_2} + {number_1} + {number_2}"

        self.assertEqual(number_placeholder_names(text), ["number_1", "number_2", "number_10"])

    def test_rejects_non_number_placeholders(self) -> None:
        self.assertFalse(has_only_number_placeholders("{number_1} и {name_1}"))
        self.assertTrue(has_only_number_placeholders("{number_1} и {number_10}"))

    def test_render_preserves_literal_segments_and_repeated_values(self) -> None:
        template_text = "Наташа дала {number_1} рублей, потом еще {number_1} рублей."

        rendered = render_template(template_text, {"number_1": 7})

        self.assertEqual(rendered, "Наташа дала 7 рублей, потом еще 7 рублей.")
        self.assertTrue(verify_literal_integrity(template_text, rendered))

    def test_generation_does_not_mutate_source_template(self) -> None:
        template = {
            "template_number": 1,
            "template_id": "synthetic_integer_00001",
            "title": "Сложение двух чисел",
            "module_name": "Арифметика",
            "answer_type": "integer",
            "answer_formula": "number_1 + number_2",
            "template_text": "Вычислите {number_1} + {number_2}.",
            "placeholders": {"numbers": ["number_1", "number_2"]},
            "original_values": {"number_1": 2, "number_2": 3},
        }
        before = copy.deepcopy(template)

        generated = generate_problem_instance(template, random.Random(5))

        self.assertEqual(template, before)
        self.assertIsInstance(generated["answer"], int)
        self.assertNotIn("{number_", generated["rendered_problem"])


if __name__ == "__main__":
    unittest.main()
