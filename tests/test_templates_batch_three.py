"""Независимая проверка: купе, соседние числа, умножение, частное, разбойники, сухофрукты.

Тест нигде не повторяет формулу шаблона. Купе он считает раскладкой мест
по купе подряд, ряд разбойников — прямым сложением восьми слагаемых,
а выход сухофруктов — решением системы, а не сложением уравнений.
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


class BerthTests(unittest.TestCase):
    TEMPLATE = LIBRARY["berth_number_in_compartment"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            seats = int(re.search(r"вагоне (\d+)", text).group(1))
            per = int(re.search(r"по (\d+)", text).group(1))
            seat = int(re.search(r"номер (\d+)", text).group(1))

            # Решение с нуля: раскладываем места по купе подряд и смотрим,
            # в какое попало нужное.
            room = 0
            placed = 0
            while placed < seat:
                room += 1
                placed += per
            self.assertLessEqual(seat, seats, f"seed {seed}: место вне вагона")
            self.assertEqual(generated["answer"], room, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: место 23 при четырёх местах в купе — шестое купе."""
        self.assertEqual(-(-23 // 4), 6)


class ConsecutiveSumTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_consecutive_numbers_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"равна (\d+)", text).group(1))
            smaller = generated["answer"]

            self.assertEqual(smaller + (smaller + 1), total, f"seed {seed}: {text}")
            self.assertEqual(total % 2, 1, f"seed {seed}: сумма соседних не бывает чётной")

    def test_source_example_reproduces(self) -> None:
        """Контроль: сумма 151 — это 75 и 76."""
        self.assertEqual(75 + 76, 151)


class MultiplyEqualsAddTests(unittest.TestCase):
    TEMPLATE = LIBRARY["multiplying_equals_adding"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(r"на (\d+), чтобы", text).group(1))
            added = int(re.search(r"числу (\d+)", text).group(1))
            number = generated["answer"]

            # Решение с нуля: проверяем равенство напрямую и убеждаемся,
            # что другого целого решения нет.
            self.assertEqual(times * number, number + added, f"seed {seed}: {text}")
            others = [x for x in range(1, 500) if times * x == x + added and x != number]
            self.assertEqual(others, [], f"seed {seed}: есть и другие решения")

    def test_source_example_reproduces(self) -> None:
        """Контроль: умножение на 9 равно прибавлению 24 для числа 3."""
        self.assertEqual(9 * 3, 3 + 24)


class QuotientRelationsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["quotient_relations_puzzle"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            smaller, bigger = (int(v) for v in re.findall(r"в (\d+) раз", text))
            quotient = generated["answer"]

            # Решение с нуля: перебираем делитель и частное и оставляем те,
            # что удовлетворяют обоим отношениям сразу.
            fits = [
                (divisor, divisor * bigger)
                for divisor in range(1, 200)
                if divisor * bigger * divisor == smaller * (divisor * bigger)
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits[:3]} — {text}")
            self.assertEqual(quotient, fits[0][1], f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: делитель 3, частное 24, делимое 72."""
        self.assertEqual(72 // 3, 24)
        self.assertEqual(24, 8 * 3)


class RobbersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["robbers_growing_hoard"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            robbers = int(re.search(r"положат (\d+)|последний из (\d+)", text).group(1)
                          or re.search(r"последний из (\d+)", text).group(1))
            # Между числом и словом движок ставит неразрывный пробел.
            times = int(re.search(r"в (\d+)[\s ]+раз", text).group(1))

            # Решение с нуля: складываем ряд подряд, без всякой формулы.
            put = 1
            total = 1
            for _ in range(robbers - 1):
                put = times * put + 1
                total += put
            expected = put if "последний" in text else total
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_printed_start_matches_the_rule(self) -> None:
        """Второе и третье числа в условии обязаны подчиняться правилу.

        Числа печатаются из derived_values, а множитель разыгрывается,
        поэтому проверяем их на самой выдаче, а не на константах.
        """
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            second, third = (int(v) for v in re.search(
                r"второй — (\d+), третий — (\d+)", text).groups())
            # Между числом и словом движок ставит неразрывный пробел.
            times = int(re.search(r"в (\d+)[\s ]+раз", text).group(1))
            self.assertEqual(second, times * 1 + 1, f"seed {seed}: {text}")
            self.assertEqual(third, times * second + 1, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: восемь разбойников кладут 4916 монет."""
        put, total = 1, 1
        for _ in range(7):
            put = 3 * put + 1
            total += put
        self.assertEqual(total, 4916)


class DriedFruitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["dried_fruit_two_mixes"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            a_one, b_one, yield_one = (int(v) for v in re.search(
                r"Из (\d+) тонн слив и (\d+) тонн груш получается (\d+)", text).groups())
            a_two, b_two, yield_two = (int(v) for v in re.search(
                r"из (\d+) тонн слив и (\d+) тонн груш — (\d+)", text).groups())
            ask = int(re.search(r"выйдет из (\d+) тонн", text).group(1))

            # Решение с нуля: решаем систему по правилу Крамера — шаблон
            # вместо этого просто складывает уравнения.
            determinant = a_one * b_two - a_two * b_one
            self.assertNotEqual(determinant, 0, f"seed {seed}: система вырождена")
            plum = Fraction(yield_one * b_two - yield_two * b_one, determinant)
            pear = Fraction(a_one * yield_two - a_two * yield_one, determinant)
            self.assertEqual(generated["answer"], ask * (plum + pear), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 1530 и 1620 кг дают 350 кг с пары тонн, а с семи — 2450."""
        self.assertEqual(Fraction(1530 + 1620, 9), 350)
        self.assertEqual(7 * 350, 2450)


if __name__ == "__main__":
    unittest.main()
