from __future__ import annotations

import unittest

from problemgen.source_index.answer_definition_cleanup import (
    discover_supported_answer_types,
    merge_rejections,
    validate_answer_definition,
)


class AnswerDefinitionCleanupTests(unittest.TestCase):
    def test_rejects_unknown_type_and_empty_formula(self) -> None:
        template = {
            "template_number": 1931,
            "template_id": "arithmetic_word_model_01931",
            "answer_type": "unknown",
            "answer_formula": "",
            "placeholders": {"numbers": ["number_1"]},
            "original_values": {"number_1": 5},
        }

        valid, reason_code, reason = validate_answer_definition(template, set())

        self.assertFalse(valid)
        self.assertEqual(reason_code, "missing_answer_definition")
        self.assertIn("answer_type='unknown'", reason)
        self.assertIn("answer_formula", reason)

    def test_accepts_supported_safe_integer_formula(self) -> None:
        template = {
            "template_number": 1,
            "template_id": "sample_00001",
            "answer_type": "integer",
            "answer_formula": "number_1 + number_2",
            "placeholders": {"numbers": ["number_1", "number_2"]},
            "original_values": {"number_1": 2, "number_2": 3},
        }
        supported = discover_supported_answer_types([template])

        valid, reason_code, reason = validate_answer_definition(template, supported)

        self.assertEqual(supported, {"integer"})
        self.assertTrue(valid, f"{reason_code}: {reason}")

    def test_rejects_undefined_formula_variables(self) -> None:
        template = {
            "template_number": 2,
            "template_id": "sample_00002",
            "answer_type": "integer",
            "answer_formula": "number_1 + missing_value",
            "placeholders": {"numbers": ["number_1"]},
            "original_values": {"number_1": 2},
        }

        valid, reason_code, _ = validate_answer_definition(template, {"integer"})

        self.assertFalse(valid)
        self.assertEqual(reason_code, "undefined_formula_placeholders")

    def test_rejects_nonexistent_validator(self) -> None:
        template = {
            "template_number": 3,
            "template_id": "sample_00003",
            "answer_type": "proof",
            "answer_formula": "missing_validator",
            "placeholders": {"numbers": []},
            "original_values": {},
        }

        valid, reason_code, _ = validate_answer_definition(template, {"proof"})

        self.assertFalse(valid)
        self.assertEqual(reason_code, "missing_answer_validator")

    def test_rejects_answer_type_mismatch(self) -> None:
        template = {
            "template_number": 4,
            "template_id": "sample_00004",
            "answer_type": "integer",
            "answer_formula": "'нет'",
            "placeholders": {"numbers": []},
            "original_values": {},
        }

        valid, reason_code, _ = validate_answer_definition(template, {"integer"})

        self.assertFalse(valid)
        self.assertEqual(reason_code, "answer_type_mismatch")

    def test_merge_rejections_keeps_unique_template_ids(self) -> None:
        previous = [{"template_id": "same", "template_number": 1, "reason_code": "old"}]
        new = [{"template_id": "same", "template_number": 1, "reason_code": "new"}]

        merged = merge_rejections(previous, new)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["reason_code"], "new")


if __name__ == "__main__":
    unittest.main()
