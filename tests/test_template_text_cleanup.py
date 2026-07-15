from __future__ import annotations

import unittest

from problemgen.source_index.text_quality_cleanup import analyze_rendered_problem, clean_template, repair_text


class TemplateTextCleanupTests(unittest.TestCase):
    def test_removes_trailing_en_fragment(self) -> None:
        text = "Найдите значение x: 2026 + (x * 37 - 1000) * 26 - 39 = 999 ен:"

        repaired, _ = repair_text(text)

        self.assertEqual(repaired, "Найдите значение x: 2026 + (x * 37 - 1000) * 26 - 39 = 999.")

    def test_removes_redundant_leading_number(self) -> None:
        text = "5. Сколько существует нечётных четырёхзначных чисел, у которых первая цифра больше последней?"

        repaired, _ = repair_text(text)

        self.assertEqual(repaired, "Сколько существует нечётных четырёхзначных чисел, у которых первая цифра больше последней?")

    def test_keeps_meaningful_initial_number(self) -> None:
        text = "5 мальчиков и 4 девочки организовали турнир."

        repaired, _ = repair_text(text)

        self.assertEqual(repaired, text)

    def test_repairs_cyrillic_letter_as_minus_in_sequence(self) -> None:
        text = "Вычислите: 3 - 4 + 6 - 7 + 9 - 10 + ... + 33 ы 35."

        repaired, _ = repair_text(text)

        self.assertEqual(repaired, "Вычислите: 3 - 4 + 6 - 7 + 9 - 10 + … + 33 - 35.")

    def test_rejects_incomplete_comparison_fragment(self) -> None:
        template = {
            "template_number": 1,
            "template_id": "bad_fragment",
            "template_text": "меньше, чем Маша. Сколько английских слов знает каждая?",
            "original_values": {},
        }

        cleaned, rejected, _ = clean_template(template)

        self.assertIsNone(cleaned)
        self.assertIsNotNone(rejected)
        assert rejected is not None
        self.assertEqual(rejected["reason_code"], "incomplete_source_text")

    def test_legitimate_algebraic_variables_are_not_flagged(self) -> None:
        result = analyze_rendered_problem("Пусть x и y — натуральные числа. Найдите x + y.")

        self.assertTrue(result["valid"], result["issues"])

    def test_unmatched_parentheses_are_flagged(self) -> None:
        result = analyze_rendered_problem("Вычислите (15 - 3.")

        self.assertFalse(result["valid"])
        self.assertIn("unmatched_parenthesis", {issue["code"] for issue in result["issues"]})


if __name__ == "__main__":
    unittest.main()
