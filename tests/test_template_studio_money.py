"""Независимая проверка новых JSON-шаблонов темы «Деньги, покупки, цены».

Не путать с tests/test_money_templates.py — тот проверяет старый Python-генератор
problemgen.generation.money_templates; этот файл — новые декларативные шаблоны
из data/template_studio/library/, заведённые по правилам
Docs/AGENT_TASK_TO_TEMPLATE_PROMPT.md.
"""
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
EQUALIZE = LIBRARY["money_equalize_pair"]
COIN_RATIO = LIBRARY["coin_ratio_three_people"]
SEEDS = range(40)


class MoneyEqualizePairTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(EQUALIZE, random.Random(seed))
            diff = generated["parameters"]["diff"]

            # Решение с нуля: у обоих было произвольное общее M (в ответ не входит).
            # giver отдаёт receiver-у сумму a: M-a = (M+a) - diff  =>  a = diff/2.
            M = 1000
            a = Fraction(diff, 2)
            self.assertEqual(a.denominator, 1, f"seed {seed}: сумма должна быть целой")
            giver_after, receiver_after = M - a, M + a
            self.assertEqual(receiver_after - giver_after, diff)
            self.assertEqual(generated["answer"], int(a), f"seed {seed}")

    def test_giver_and_receiver_are_distinct(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(EQUALIZE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["giver"].character_id, values["receiver"].character_id)

    def test_text_is_well_formed(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(EQUALIZE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text)
            self.assertNotIn("  ", text)
            self.assertTrue(text.endswith("?"))
            self.assertTrue(text[0].isupper())


class CoinRatioThreePeopleTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(COIN_RATIO, random.Random(seed))
            values = generated["parameters"]
            total, diff2, relation = values["total"], values["diff2"], values["relation"]
            ratio = Fraction(values["ratio"])

            # Независимое решение: составляем линейное уравнение заново из
            # словесного условия, не используя derived_values шаблона.
            if relation == "меньше":
                # a монет у героя, b = ratio*a (герой в ratio раз меньше b), c = a - diff2.
                a = (total + diff2) / (ratio + 2)
                b = ratio * a
            else:
                # a = ratio*b (герой в ratio раз больше b) => b = a/ratio, c = a - diff2.
                a = (total + diff2) * ratio / (2 * ratio + 1)
                b = a / ratio
            c = a - diff2

            self.assertEqual(a.denominator, 1, f"seed {seed}: количество монет должно быть целым")
            self.assertEqual(b.denominator, 1, f"seed {seed}: количество монет b должно быть целым")
            self.assertGreater(a, 0)
            self.assertGreater(b, 0)
            self.assertGreater(c, 0)
            self.assertEqual(a + b + c, total, f"seed {seed}: сумма должна совпасть с условием")
            self.assertEqual(generated["answer"], int(a), f"seed {seed}")

    def test_three_distinct_characters(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(COIN_RATIO, random.Random(seed))["parameters"]
            ids = {values["a"].character_id, values["b"].character_id, values["c"].character_id}
            self.assertEqual(len(ids), 3)

    def test_text_is_well_formed(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(COIN_RATIO, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text)
            self.assertNotIn("  ", text)
            self.assertTrue(text.endswith("?"))
            self.assertTrue(text[0].isupper())
            self.assertIn(" раз", text)  # движок ставит неразрывный пробел перед словом


if __name__ == "__main__":
    unittest.main()
