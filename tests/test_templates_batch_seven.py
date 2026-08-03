"""Независимая проверка: пираты, всадники, обмен валют, разбиение на пары.

Пиратов тест прогоняет вперёд по всем трём передачам. Всадников расставляет
по четырём направлениям. Обмен ведёт по звеньям в обратную сторону.
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


class ThreePiratesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_pirates_redistribution"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"делили (\d+)", text).group(1))
            start_a = generated["answer"]

            # Решение с нуля: прогоняем все три передачи вперёд и требуем,
            # чтобы в конце вышло поровну. Доли двух других находим перебором.
            fits = []
            for start_b in range(1, total):
                start_c = total - start_a - start_b
                if start_c < 1:
                    continue
                a, b, c = start_a, start_b, start_c
                a, b, c = a - b - c, 2 * b, 2 * c
                b, c, a = b - c - a, 2 * c, 2 * a
                c, a, b = c - a - b, 2 * a, 2 * b
                if a == b == c and a > 0:
                    fits.append((start_b, start_c))
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits[:3]} — {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 120 монет — начальные доли 65, 35 и 20."""
        a, b, c = 65, 35, 20
        a, b, c = a - b - c, 2 * b, 2 * c
        b, c, a = b - c - a, 2 * c, 2 * a
        c, a, b = c - a - b, 2 * a, 2 * b
        self.assertEqual((a, b, c), (40, 40, 40))


class RidersDistanceTests(unittest.TestCase):
    TEMPLATE = LIBRARY["riders_on_one_road_distance"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            distance = int(re.search(r"равно (\d+) лье", text).group(1))
            speed_a = int(re.search(r"покрывает (\d+) лье", text).group(1))
            speed_b = int(re.search(r"— (\d+) лье", text).group(1))

            # Решение с нуля: ставим всадников на прямую и разводим их
            # по всем четырём сочетаниям направлений.
            found = set()
            for step_a in (-speed_a, speed_a):
                for step_b in (-speed_b, speed_b):
                    found.add(abs((distance + step_b) - step_a))
            self.assertEqual(set(generated["answer"]), found, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 20 лье при 4 и 5 дают 11, 19, 21 и 29."""
        found = {abs((20 + b) - a) for a in (-4, 4) for b in (-5, 5)}
        self.assertEqual(found, {11, 19, 21, 29})


class ExchangeChainTests(unittest.TestCase):
    TEMPLATE = LIBRARY["currency_exchange_chain"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            a_give, a_get = (int(v) for v in re.search(
                r"за (\d+) тугриков дают (\d+)", text).groups())
            b_give, b_get = (int(v) for v in re.search(
                r"за (\d+) рупий — (\d+)", text).groups())
            c_give, c_get = (int(v) for v in re.search(
                r"а за (\d+) крон — (\d+)", text).groups())
            krones = int(re.search(r"за (\d+) крон\?", text).group(1))

            # Решение с нуля: считаем дробями, звено за звеном.
            rupees = Fraction(krones, c_give) * c_get
            dinars = Fraction(rupees, b_give) * b_get
            tugriks = Fraction(dinars, a_get) * a_give
            self.assertEqual(tugriks.denominator, 1, f"seed {seed}: не целые тугрики")
            self.assertEqual(generated["answer"], int(tugriks), f"seed {seed}: {text}")


class PairingTests(unittest.TestCase):
    TEMPLATE = LIBRARY["pairing_numbers_equal_sums"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            last = int(re.search(r"до (\d+)", text).group(1))

            # Решение с нуля: строим сами пары и проверяем, что суммы равны.
            pairs = [(k, last + 1 - k) for k in range(1, last // 2 + 1)]
            sums = {a + b for a, b in pairs}
            self.assertEqual(len(sums), 1, f"seed {seed}: суммы пар разные")
            self.assertEqual(generated["answer"], sums.pop(), f"seed {seed}: {text}")
            self.assertEqual(sum(a + b for a, b in pairs), last * (last + 1) // 2,
                             f"seed {seed}: пары покрывают не все числа")

    def test_source_example_reproduces(self) -> None:
        """Контроль: от 1 до 100 сумма каждой пары равна 101."""
        self.assertEqual(1 + 100, 101)
        self.assertEqual(50 * 101, 5050)


if __name__ == "__main__":
    unittest.main()
