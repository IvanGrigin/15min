"""Независимая проверка лифта с двумя кнопками и вычёркивания цифр.

Лифт решается перебором маршрутов в глубину с ограничением по длине — путь,
отличный от обхода в ширину, которым считает шаблон. Совпадение двух разных
обходов и есть проверка.

Вычёркивание проверяется прямым перебором подстрок: тест собирает все
последовательности оставленных цифр сам и складывает различные значения.

Отдельно закреплено то, из-за чего задача про лифт вообще нетривиальна:
дом ограничен, и рассуждение через наибольший общий делитель шагов даёт
неверный ответ. В доме из восьми этажей кнопками «+7» и «−9» с первого
этажа достижимы только первый и восьмой, хотя gcd(7, 9) = 1.
"""
from __future__ import annotations

import math
import random
import re
import sys
import unittest
from itertools import combinations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)


class ElevatorTests(unittest.TestCase):
    TEMPLATE = LIBRARY["elevator_two_buttons"]

    def shortest(self, floors: int, start: int, target: int, up: int, down: int) -> int:
        """Поиск в глубину с постепенно растущим пределом длины пути."""
        for limit in range(1, 40):
            stack = [(start, 0)]
            best_seen: dict[int, int] = {}
            while stack:
                floor, steps = stack.pop()
                if floor == target:
                    return steps
                if steps >= limit:
                    continue
                if best_seen.get(floor, 99) <= steps:
                    continue
                best_seen[floor] = steps
                for nxt in (floor + up, floor - down):
                    if 1 <= nxt <= floors:
                        stack.append((nxt, steps + 1))
        raise AssertionError("путь не найден")

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            floors = int(re.search(r"В доме (\d+) этаж", text).group(1))
            up = int(re.search(r"поднимает на (\d+)", text).group(1))
            down = int(re.search(r"опускает на (\d+)", text).group(1))
            start = int(re.search(r"с (\d+)-го этажа", text).group(1))
            target = int(re.search(r"на (\d+)-й\?", text).group(1))

            self.assertEqual(
                generated["answer"], self.shortest(floors, start, target, up, down),
                f"seed {seed}: {text}")

    def test_house_bounds_really_matter(self) -> None:
        """Иначе задача сводилась бы к наибольшему общему делителю шагов."""
        reachable = {1}
        frontier = [1]
        while frontier:
            floor = frontier.pop()
            for nxt in (floor + 7, floor - 9):
                if 1 <= nxt <= 8 and nxt not in reachable:
                    reachable.add(nxt)
                    frontier.append(nxt)
        self.assertEqual(reachable, {1, 8})
        self.assertEqual(math.gcd(7, 9), 1, "по НОД достижимо было бы всё")

    def test_answer_is_within_reason(self) -> None:
        for seed in SEEDS:
            answer = generate_active_template(
                self.TEMPLATE, random.Random(seed))["answer"]
            self.assertGreaterEqual(answer, 4, f"seed {seed}: слишком просто")
            self.assertLessEqual(answer, 25, f"seed {seed}: слишком длинно")


class DigitDeletionTests(unittest.TestCase):
    TEMPLATE = LIBRARY["digit_deletion_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            number = re.search(r"число (\d+)\.", text).group(1)
            length = int(re.search(r"(\d+)-значные", text).group(1))

            # Перебор оставляемых позиций: порядок цифр сохраняется,
            # ведущий ноль не даёт числа нужной длины.
            distinct = {
                int("".join(number[index] for index in keep))
                for keep in combinations(range(len(number)), length)
                if number[keep[0]] != "0"
            }
            self.assertEqual(generated["answer"], sum(distinct), f"seed {seed}: {text}")

    def test_repeats_are_counted_once(self) -> None:
        """Слово «различных» и есть задача: наборов позиций больше, чем чисел."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            number = re.search(r"число (\d+)\.", text).group(1)
            length = int(re.search(r"(\d+)-значные", text).group(1))
            placements = list(combinations(range(len(number)), length))
            distinct = {"".join(number[index] for index in keep) for keep in placements}
            self.assertLess(len(distinct), len(placements),
                            f"seed {seed}: повторов нет, задача теряет смысл")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику: из 2525252 выходит 15 чисел с суммой 56661."""
        number = "2525252"
        distinct = {
            int("".join(number[index] for index in keep))
            for keep in combinations(range(7), 4)
        }
        self.assertEqual(len(distinct), 15)
        self.assertEqual(sum(distinct), 56661)


class SpilledWaterTests(unittest.TestCase):
    """Перевод единиц: литр — это кубический дециметр."""

    TEMPLATE = LIBRARY["spilled_water_layer"]

    def test_matches_independent_solution(self) -> None:
        from fractions import Fraction

        parts = {"наполовину": Fraction(1, 2), "на четверть": Fraction(1, 4),
                 "на три четверти": Fraction(3, 4), "полностью": Fraction(1)}
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            room_a, room_b = (int(v) for v in re.search(r"(\d+) м × (\d+) м", text).groups())
            volume = int(re.search(r"объёмом (\d+)", text).group(1))
            share = next(value for word, value in parts.items() if word in text)

            # Решение с нуля: вода в кубических дециметрах, пол в квадратных
            # дециметрах, высота переводится в миллиметры умножением на 100.
            water = Fraction(volume) * share
            floor = Fraction(room_a * 10 * room_b * 10)
            height_mm = water / floor * 100
            self.assertEqual(height_mm.denominator, 1, f"seed {seed}: не целое — {text}")
            self.assertEqual(generated["answer"], int(height_mm), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику: 3 × 4 м, 120 л наполовину — 5 мм."""
        from fractions import Fraction
        self.assertEqual(Fraction(120, 2) / Fraction(30 * 40) * 100, 5)


class PlanksTests(unittest.TestCase):
    """Округление вниз при раскрое и вверх при закупке."""

    TEMPLATE = LIBRARY["planks_to_buy"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            piece = int(re.search(r"длиной (\d+) см", text).group(1))
            need = int(re.search(r"количестве (\d+)", text).group(1))
            sold = int(re.search(r"длиной (\d+) м\.", text).group(1)) * 100

            # Решение с нуля: режем по одной доске, пока не наберём нужное.
            cut = 0
            bought = 0
            while cut < need:
                bought += 1
                cut += sold // piece
            self.assertEqual(generated["answer"], bought, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 112 досок по 75 см из четырёхметровых — 23 доски."""
        self.assertEqual(-(-112 // (400 // 75)), 23)


if __name__ == "__main__":
    unittest.main()
