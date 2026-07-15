from __future__ import annotations

import copy
from pathlib import Path
import random
import unittest

from problemgen.web.worksheet_site import render_site_page
from problemgen.worksheet.all_tasks_site import (
    catalog_metadata,
    filter_eligible_templates,
    generate_problem_instance,
    has_only_number_placeholders,
    number_placeholder_names,
    render_template,
    verify_literal_integrity,
)


class WorksheetSiteTests(unittest.TestCase):
    def test_site_renders_five_template_selectors(self) -> None:
        page = render_site_page()

        self.assertEqual(page.count("data-template-select="), 5)
        self.assertEqual(page.count("data-template-search="), 5)
        self.assertIn("Генератор математических задач", page)
        self.assertIn("Выберите пять шаблонов", page)
        self.assertIn("Сгенерировать вариант", page)
        self.assertIn("Показать ответы", page)

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
