"""Независимая проверка: лебедь, торговец, упаковка, пять точек, вес, чай.

Тест каждый раз пересчитывает задачу по напечатанному условию своим путём:
речь стаи собирает по долям, сделки торговца проводит по очереди, точки
на прямой расставляет координатами, а цену чая ищет перебором копеек.
"""
from __future__ import annotations

import random
import re
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
SEEDS = range(25)


class SwanRiddleTests(unittest.TestCase):
    TEMPLATE = LIBRARY["swan_and_flock_riddle"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            claim = int(re.search(r"Здравствуйте, (\d+)", text).group(1))
            flock = generated["answer"]

            # Решение с нуля: собираем речь стаи по кускам и сверяем с числом.
            same = flock
            half = Fraction(flock, 2)
            quarter = Fraction(flock, 4)
            self.assertEqual(flock + same + half + quarter + 1, claim,
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: сто птиц дают стаю из 36 гусей."""
        self.assertEqual(36 + 36 + Fraction(36, 2) + Fraction(36, 4) + 1, 100)


class MerchantTests(unittest.TestCase):
    TEMPLATE = LIBRARY["merchant_buys_and_sells_twice"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            prices = [int(v) for v in re.findall(r"за (\d+)", text)]
            self.assertEqual(len(prices), 4, f"seed {seed}: {text}")
            buy_one, sell_one, buy_two, sell_two = prices

            # Решение с нуля: ведём кошелёк по сделкам, начиная с нуля.
            purse = 0
            purse -= buy_one
            purse += sell_one
            purse -= buy_two
            purse += sell_two
            self.assertEqual(generated["answer"], purse, f"seed {seed}: {text}")

    def test_second_purchase_is_dearer(self) -> None:
        """Иначе исчезает спор, ради которого задача и придумана."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            prices = [int(v) for v in re.findall(r"за (\d+)", text)]
            self.assertGreater(prices[2], prices[1], f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 7, 8, 9, 10 — прибыль 2 монеты."""
        self.assertEqual(-7 + 8 - 9 + 10, 2)


class ShopPackTests(unittest.TestCase):
    TEMPLATE = LIBRARY["shop_pack_resale_profit"]

    SHARES = {"две трети": Fraction(2, 3), "три четверти": Fraction(3, 4),
              "половину": Fraction(1, 2), "три пятых": Fraction(3, 5),
              "четыре пятых": Fraction(4, 5), "пять шестых": Fraction(5, 6)}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            cost = int(re.search(r"заплатил (\d+)", text).group(1))
            sold = self.SHARES[re.search(r"Продав (\S+ ?\S*) упаковки", text).group(1)]
            back = self.SHARES[re.search(r"вернул (\S+ ?\S*) потраченных", text).group(1)]

            # Решение с нуля: цена одной доли товара — это выручка, делённая
            # на проданную долю. За всю упаковку выручится столько же на целое.
            revenue_all = Fraction(cost) * back / sold
            self.assertEqual(generated["answer"], revenue_all - cost, f"seed {seed}: {text}")
            self.assertGreater(revenue_all, cost, f"seed {seed}: торговля в убыток")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 1000 рублей, две трети за три четверти денег — прибыль 125."""
        self.assertEqual(Fraction(1000) * Fraction(3, 4) / Fraction(2, 3) - 1000, 125)


class FivePointsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["five_points_on_line"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            ab = int(re.search(r"AB = (\d+)", text).group(1))
            ce = int(re.search(r"CE = (\d+)", text).group(1))

            # Решение с нуля: расставляем точки координатами. BC неизвестно,
            # поэтому пробуем разные — ответ обязан от него не зависеть.
            answers = set()
            for bc in range(1, 40):
                a = 0
                b = a + ab
                c = b + bc
                d = c + (c - a) - (c - b)   # AC = BD даёт CD = AB
                e = c + ce
                if d < e:
                    answers.add(e - d)
            self.assertEqual(answers, {ce - ab}, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], ce - ab, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: AB = 23 и CE = 101 дают DE = 78."""
        self.assertEqual(101 - 23, 78)


class WeightChainTests(unittest.TestCase):
    TEMPLATE = LIBRARY["weight_chain_transitivity"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            heavy, middle = re.search(r"^(\S+) тяжелее, чем (\S+),", text).groups()
            light = re.search(r"а \S+ тяжелее, чем (\S+)\.", text).groups()[0]

            # Решение с нуля: строим порядок по двум сравнениям и берём
            # больший из двух названных в вопросе.
            order = {light: 0, middle: 1, heavy.lower(): 2}
            asked = re.search(r"— (\S+) или (\S+)\?", text).groups()
            heavier = max(asked, key=lambda name: order[name])
            self.assertEqual(generated["answer_text"].lower(), heavier.lower(),
                             f"seed {seed}: {text}")

    def test_question_reverses_the_order(self) -> None:
        """Ответ нельзя дать по порядку слов: спрашивают лёгкое первым."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            first_asked = re.search(r"— (\S+) или", text).group(1)
            self.assertNotEqual(first_asked.lower(),
                                text.split()[0].lower(), f"seed {seed}: {text}")


class TeaPriceTests(unittest.TestCase):
    TEMPLATE = LIBRARY["tea_price_between_bounds"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            cheap_count = int(re.search(r"что (\d+)", text).group(1))
            cheap_roubles = int(re.search(r"дешевле (\d+)", text).group(1))
            dear_count = int(re.search(r"а (\d+) стакан", text).group(1))
            dear_roubles = int(re.search(r"дороже (\d+)", text).group(1))

            # Решение с нуля: перебираем цену в копейках.
            fits = [
                price for price in range(1, 100000)
                if cheap_count * price < cheap_roubles * 100
                and dear_count * price > dear_roubles * 100
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits[:4]} — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 9 стаканов дешевле 10 рублей, 10 дороже 11 — 111 копеек."""
        fits = [p for p in range(1, 1000) if 9 * p < 1000 and 10 * p > 1100]
        self.assertEqual(fits, [111])


if __name__ == "__main__":
    unittest.main()
