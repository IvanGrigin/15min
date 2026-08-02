"""Независимая проверка четырёх задач волны 2: гири, цепочка цифр, поезда, поиск N.

Каждый решатель теста идёт своим путём. Цепочка последних цифр в шаблоне
находится через предпериод и период, а тест просто считает члены подряд —
медленно, зато прямо. Наименьшее N шаблон ищет перебором снизу, тест тоже,
но проверяет заодно, что меньших подходящих чисел нет. Гири и вагоны
пересчитываются полным перебором комбинаций и делителей.
"""
from __future__ import annotations

import math
import random
import re
import sys
import unittest
from itertools import product
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)


class TrainCarsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["train_cars_common_size"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            seats = [int(v) for v in re.search(
                r"мест: (\d+), (\d+) и (\d+)", text).groups()]
            limit = int(re.search(r"больше (\d+)", text).group(1))

            # Решение с нуля: перебираем вместимость вагона и оставляем ту,
            # что делит все три числа и больше предела.
            fits = [
                size for size in range(limit + 1, min(seats) + 1)
                if all(value % size == 0 for value in seats)
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходит {fits} — {text}")
            self.assertEqual(generated["answer"],
                             sum(value // fits[0] for value in seats),
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 236, 295 и 472 места дают 17 вагонов по 59 мест."""
        self.assertEqual(math.gcd(math.gcd(236, 295), 472), 59)
        self.assertEqual(236 // 59 + 295 // 59 + 472 // 59, 17)


class WeightsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["weights_on_two_pans"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            weights = [int(v) for v in re.findall(r"(\d+) кг", text)]

            # Решение с нуля: гиря лежит рядом с грузом, напротив или в стороне.
            found = {
                abs(sum(weight * sign for weight, sign in zip(weights, signs)))
                for signs in product((-1, 0, 1), repeat=len(weights))
            } - {0}
            self.assertEqual(generated["answer"], len(found), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: гири 1, 2 и 9 отмеряют десять весов."""
        found = {abs(a * 1 + b * 2 + c * 9)
                 for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)} - {0}
        self.assertEqual(sorted(found), [1, 2, 3, 6, 7, 8, 9, 10, 11, 12])


class DigitChainTests(unittest.TestCase):
    TEMPLATE = LIBRARY["last_digit_chain"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shown = [int(v) for v in re.findall(r"(\d)(?=[,\s])", text)][:2]
            position = int(re.search(r"на (\d+)-м месте", text).group(1))
            multiply = "произведения" in text

            # Решение с нуля: считаем члены подряд до нужного места.
            # Шаблон ищет период — тест намеренно этого не делает.
            chain = list(shown)
            while len(chain) < position:
                previous, last = chain[-2], chain[-1]
                chain.append((previous * last if multiply else previous + last) % 10)
            self.assertEqual(generated["answer"], chain[position - 1], f"seed {seed}: {text}")

    def test_printed_start_matches_the_rule(self) -> None:
        """Первые семь членов в условии обязаны подчиняться правилу."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            shown = [int(v) for v in re.findall(r"(\d)(?=[,\s])", text)][:7]
            multiply = "произведения" in text
            for index in range(2, len(shown)):
                expected = (shown[index - 2] * shown[index - 1] if multiply
                            else shown[index - 2] + shown[index - 1]) % 10
                self.assertEqual(shown[index], expected, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: цепочка 1, 2 с произведением на 2021-м месте даёт 8."""
        chain = [1, 2]
        while len(chain) < 2021:
            chain.append((chain[-2] * chain[-1]) % 10)
        self.assertEqual(chain[:7], [1, 2, 2, 4, 8, 2, 6])
        self.assertEqual(chain[2020], 8)


class SmallestByDigitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["smallest_number_by_digit_count"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shift_a, shift_b = (int(v) for v in re.search(
                r"N \+ (\d+) и N \+ (\d+)", text).groups())
            wanted, digit = re.search(r"ровно (\d+) цифр\S* (\d)", text).groups()
            wanted = int(wanted)

            def total(value: int) -> int:
                written = f"{value}{value + shift_a}{value + shift_b}"
                return written.count(digit)

            answer = generated["answer"]
            self.assertEqual(total(answer), wanted, f"seed {seed}: {text}")
            # И ни одного меньшего подходящего — иначе ответ не наименьший.
            smaller = [value for value in range(1, answer) if total(value) == wanted]
            self.assertEqual(smaller, [], f"seed {seed}: есть меньшие {smaller[:3]}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: сдвиги 239 и 1000, три семёрки — наименьшее N равно 37."""
        def total(value: int) -> int:
            return f"{value}{value + 239}{value + 1000}".count("7")
        self.assertEqual(total(37), 3)
        self.assertEqual([v for v in range(1, 37) if total(v) == 3], [])


if __name__ == "__main__":
    unittest.main()
