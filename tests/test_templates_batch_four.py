"""Независимая проверка: три числа, многоугольник, подарки, кран, подарок, мороженое.

Тест собирает каждую задачу заново из напечатанного условия: три числа
складывает по цифрам, подарки раздаёт по кругу по одному ребёнку, воду
наливает по секундам, а взносы за подарок пересчитывает через равные доли.
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


class ThreeNumbersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_numbers_same_but_one_digit"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"сумма равна (\d+)", text).group(1))
            tail = int(re.search(r"оканчиваются на (\d+)", text).group(1))

            # Решение с нуля: перебираем три первые цифры. Троек подходит
            # несколько, и тест требует, чтобы сумма первых цифр у всех
            # найденных троек была одна и та же — иначе ответа нет.
            fits = [
                (a, b, c)
                for a in range(1, 10) for b in range(a + 1, 10) for c in range(b + 1, 10)
                if 100 * (a + b + c) + 3 * tail == total
            ]
            self.assertTrue(fits, f"seed {seed}: ни одной тройки — {text}")
            sums = {a + b + c for a, b, c in fits}
            self.assertEqual(len(sums), 1, f"seed {seed}: суммы расходятся {sums}")
            self.assertEqual(generated["answer"], sums.pop(), f"seed {seed}: {text}")
            self.assertEqual(sum(100 * digit + tail for digit in fits[0]), total,
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 166 + 366 + 566 = 1098, сумма первых цифр 9."""
        self.assertEqual(166 + 366 + 566, 1098)
        self.assertEqual(1 + 3 + 5, 9)


class PolygonSplitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["polygon_split_from_one_vertex"]

    NAMES = {"пятиугольник": 5, "шестиугольник": 6, "восьмиугольник": 8,
             "десятиугольник": 10, "двенадцатиугольник": 12,
             "двадцатиугольник": 20, "стоугольник": 100}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            sides = next(n for name, n in self.NAMES.items() if name in text)

            # Решение с нуля: считаем диагонали из вершины и прибавляем один.
            # Каждая диагональ отрезает по треугольнику, плюс последний кусок.
            diagonals = sides - 3
            self.assertEqual(generated["answer"], diagonals + 1, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: двадцатиугольник делится на 18 треугольников."""
        self.assertEqual(20 - 2, 18)


class SantaGiftsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["santa_gifts_around_circle"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            small, big = (int(v) for v in re.search(
                r"первому — (\d+), второму — (\d+)", text).groups())
            total = int(re.search(r"раздал (\d+)", text).group(1))

            # Решение с нуля: раздаём подарки по одному ребёнку, пока хватает.
            left = total
            children = 0
            while True:
                gift = small if children % 2 == 0 else big
                if left < gift:
                    break
                left -= gift
                children += 1
            self.assertEqual(left, 0, f"seed {seed}: подарки кончились не ровно — {text}")
            self.assertEqual(generated["answer"], children, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 55 подарков по схеме 1, 2 достаются 37 детям."""
        left, children = 55, 0
        while True:
            gift = 1 if children % 2 == 0 else 2
            if left < gift:
                break
            left -= gift
            children += 1
        self.assertEqual((left, children), (0, 37))


class JarAndGlassTests(unittest.TestCase):
    TEMPLATE = LIBRARY["jar_and_glass_filling_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            volume = int(re.search(r"объёмом (\d+)\s?литр", text).group(1))
            minutes = int(re.search(r"за (\d+)", text).group(1))
            glass = int(re.search(r"входит (\d+) миллилитр", text).group(1))

            # Решение с нуля: считаем поток в миллилитрах за секунду.
            per_second = Fraction(volume * 1000, minutes * 60)
            seconds = Fraction(glass) / per_second
            self.assertEqual(seconds.denominator, 1, f"seed {seed}: не целые секунды")
            self.assertEqual(generated["answer"], int(seconds), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 3 литра за 7 минут — стакан 250 мл за 35 секунд."""
        self.assertEqual(Fraction(250) / Fraction(3000, 420), 35)


class GiftSplitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["gift_split_unknown_share"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            given = [int(v) for v in re.findall(r"(\d+)\s?рубл", text)]
            *known, refund = given
            self.assertEqual(len(known), 3, f"seed {seed}: {text}")
            unknown = generated["answer"]

            # Решение с нуля: складываем все взносы, делим на четверых
            # и проверяем, что первому вернули ровно его превышение.
            total = sum(known) + unknown
            self.assertEqual(total % 4, 0, f"seed {seed}: доли не целые — {text}")
            share = total // 4
            self.assertEqual(known[0] - share, refund, f"seed {seed}: {text}")

    def test_refund_is_the_excess(self) -> None:
        """Возврат обязан быть положительным: иначе первому не переплатили."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            refund = int(re.findall(r"(\d+)\s?рубл", text)[-1])
            self.assertGreater(refund, 0, f"seed {seed}: {text}")


class IceCreamTests(unittest.TestCase):
    TEMPLATE = LIBRARY["ice_cream_shortfall"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(r"в (\d+) раз\S* больше", text).group(1))
            scoops = int(re.search(r"ровно (\d+) морожен", text).group(1))
            money = int(re.search(r"было (\d+) рубл", text).group(1))
            price = generated["answer"]

            # Решение с нуля: проверяем оба условия задачи напрямую.
            short = 2 * price - money
            self.assertGreaterEqual(money, price, f"seed {seed}: не хватает и на одно")
            self.assertLess(money, 2 * price, f"seed {seed}: хватает и на два")
            self.assertEqual(money + times * short, scoops * price, f"seed {seed}: {text}")

    def test_source_shape_holds(self) -> None:
        """Контроль смысла: добавка выражена через нехватку, а не через цену."""
        price, money = 40, 30
        short = 2 * price - money
        self.assertEqual(short, 50)
        self.assertEqual(money + 2 * short, 130)


if __name__ == "__main__":
    unittest.main()
