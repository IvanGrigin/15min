"""Независимая проверка шаблонов темы «Работа, производительность и совместные действия»."""
from __future__ import annotations

import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SETTLEMENT = LIBRARY["joint_payment_settlement"]
WORK_RATE = LIBRARY["joint_work_rate_sum"]
SEEDS = range(40)


class JointPaymentSettlementTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(SETTLEMENT, random.Random(seed))
            values = generated["parameters"]
            total, paid_b, loan = values["total"], values["paid_b"], values["loan"]

            # Решение с нуля, без обращения к derived_values шаблона:
            # оба должны заплатить по total/2. b заплатил paid_b по счёту,
            # a заплатил остаток (total-paid_b). Раздельно есть личный заём
            # loan, который b должен a. Сводим два долга в один нетто-платёж.
            fair_share = Fraction(total, 2)
            self.assertEqual(fair_share.denominator, 1, f"seed {seed}: total должен делиться пополам")
            paid_a = total - paid_b
            self.assertGreater(paid_a, 0)
            # Если b переплатил свою долю — a должен вернуть излишек b.
            bill_owed_by_a_to_b = paid_b - fair_share
            net_owed_by_b_to_a = loan - bill_owed_by_a_to_b
            self.assertGreater(net_owed_by_b_to_a, 0, f"seed {seed}: платёж должен быть положительным")
            self.assertEqual(generated["answer"], int(net_owed_by_b_to_a), f"seed {seed}")

    def test_a_and_b_are_distinct(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(SETTLEMENT, random.Random(seed))["parameters"]
            self.assertNotEqual(values["a"].character_id, values["b"].character_id)

    def test_text_is_well_formed(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(SETTLEMENT, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text)
            self.assertNotIn("  ", text)
            self.assertTrue(text.endswith("?"))
            self.assertTrue(text[0].isupper())


class JointWorkRateSumTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(WORK_RATE, random.Random(seed))
            values = generated["parameters"]
            count_a, hours_a = values["count_a"], values["hours_a"]
            count_b, hours_b = values["count_b"], values["hours_b"]

            # Независимое решение в точных дробях (Fraction), не через
            # derived_values шаблона (там целочисленный cross//denom).
            rate_a = Fraction(count_a, hours_a)
            rate_b = Fraction(count_b, hours_b)
            total_per_hour = rate_a + rate_b
            self.assertEqual(total_per_hour.denominator, 1, f"seed {seed}: сумма темпов должна быть целой")
            self.assertNotEqual(rate_a, rate_b, f"seed {seed}: темпы не должны совпадать")
            self.assertEqual(generated["answer"], int(total_per_hour), f"seed {seed}")

    def test_answer_agrees_with_chosen_activity_word(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(WORK_RATE, random.Random(seed))
            activity = generated["parameters"]["activity"].nom
            answer_text = generated["answer_text"]
            # activity в им.п. ед.ч. — "олимпиада"/"викторина"; в ответе форма
            # согласована с числом (мн.ч.), но общий корень слова должен совпасть.
            stem = activity[:-1]
            self.assertIn(stem, answer_text, f"seed {seed}: единица ответа не совпадает со словом в условии")

    def test_text_is_well_formed(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(WORK_RATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text)
            self.assertNotIn("  ", text)
            self.assertTrue(text.endswith("."))
            self.assertTrue(text[0].isupper())


if __name__ == "__main__":
    unittest.main()
