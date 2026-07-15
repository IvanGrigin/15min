from __future__ import annotations

import re
import unittest

from problemgen.source_index.template_cleanup import (
    clean_template_record,
    comparable,
    reconstruct,
    validate_clean_catalog,
)


class AllTasksTemplateCleanupTests(unittest.TestCase):
    def test_cleanup_keeps_only_number_placeholders(self) -> None:
        template = {
            "template_number": 1,
            "template_id": "sample_00001",
            "source_problem_id": 10,
            "source_problem_number": 20,
            "module_id": "sample",
            "difficulty": 4,
            "source_text": "Наташа и Соня составляют 13 олимпиад за 2 часа.",
            "template_text": "{Entity_number_1} и {Entity_number_2} составляют {number_1} олимпиад за {number_2} часа.",
        }

        cleaned, rejected, _ = clean_template_record(template, 1)

        self.assertIsNone(rejected)
        self.assertIsNotNone(cleaned)
        assert cleaned is not None
        self.assertEqual(
            cleaned["template_text"],
            "Наташа и Соня составляют {number_1} олимпиад за {number_2} часа.",
        )
        self.assertEqual(cleaned["placeholders"], {"numbers": ["number_1", "number_2"]})
        self.assertFalse(re.search(r"{(?!number_[1-9]\d*})[^}]+}", cleaned["template_text"]))

    def test_reconstruction_preserves_cleaned_source_text(self) -> None:
        template = {
            "template_number": 2,
            "template_id": "sample_00002",
            "source_problem_id": 11,
            "source_problem_number": 21,
            "module_id": "sample",
            "difficulty": 4,
            "source_text": "На электронных часах высвечивается13:00:07.",
            "template_text": "",
        }

        cleaned, _, _ = clean_template_record(template, 1)

        assert cleaned is not None
        rebuilt = reconstruct(cleaned["template_text"], cleaned["original_values"])
        self.assertEqual(comparable(rebuilt), comparable(cleaned["source_text"]))

    def test_validation_reports_no_failures_for_cleaned_template(self) -> None:
        template = {
            "template_number": 3,
            "template_id": "sample_00003",
            "source_problem_id": 12,
            "source_problem_number": 22,
            "module_id": "sample",
            "difficulty": 4,
            "source_text": "Вычислите1002 + 499.",
            "template_text": "",
        }
        cleaned, rejected, _ = clean_template_record(template, 1)

        assert cleaned is not None
        stats = validate_clean_catalog([cleaned], [] if rejected is None else [rejected], 1)

        self.assertEqual(stats["forbidden_placeholders_remaining"], 0)
        self.assertEqual(stats["reconstruction_tests_failed"], 0)
        self.assertEqual(stats["metadata_failures"], [])


if __name__ == "__main__":
    unittest.main()
