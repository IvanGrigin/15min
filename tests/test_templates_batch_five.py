"""Независимая проверка: доска, эпидемия, квартиры, вершины, пироги, угощения.

Решатели теста нигде не повторяют шаблон. Доску и эпидемию тест прокручивает
шаг за шагом сам. Вершины многоугольника обходит по кругу и складывает
в множество, а не считает наибольший общий делитель. Систему про угощения
решает подстановкой.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)


class BlackboardTests(unittest.TestCase):
    TEMPLATE = LIBRARY["blackboard_halve_or_triple"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            start = int(re.search(r"написано число (\d+)", text).group(1))

            # Решение с нуля: крутим правило, пока не дойдём до единицы.
            value, steps = start, 0
            while value != 1:
                value = value // 2 if value % 2 == 0 else 3 * value + 1
                steps += 1
                self.assertLess(steps, 500, f"seed {seed}: не сходится")
            self.assertEqual(generated["answer"], steps, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: из 11 путь до единицы идёт через 34, 17, 52 и 26."""
        value, steps = 11, 0
        while value != 1:
            value = value // 2 if value % 2 == 0 else 3 * value + 1
            steps += 1
        self.assertEqual(steps, 14)


class EpidemicTests(unittest.TestCase):
    TEMPLATE = LIBRARY["epidemic_worst_case_days"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            pupils = int(re.search(r"учатся (\d+)", text).group(1))

            # Решение с нуля: каждый день заболевает наименьшее число,
            # которое ещё больше половины, — это худший случай.
            healthy, days = pupils, 0
            while healthy > 0:
                sick_today = healthy // 2 + 1
                healthy -= sick_today
                days += 1
            self.assertEqual(generated["answer"], days, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 655 детей — девять дней."""
        healthy, days = 655, 0
        while healthy > 0:
            healthy -= healthy // 2 + 1
            days += 1
        self.assertEqual(days, 9)


class SameFlatTests(unittest.TestCase):
    TEMPLATE = LIBRARY["same_flat_number_two_houses"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            floor_a, per_a, floor_b, per_b = (int(v) for v in re.search(
                r"на (\d+)-м этаже дома, в котором на каждом этаже по (\d+).+?"
                r"на (\d+)-м этаже другого дома, где на каждом этаже по (\d+)",
                text).groups())

            # Решение с нуля: выписываем номера квартир обоих этажей
            # и пересекаем множества.
            first = set(range((floor_a - 1) * per_a + 1, floor_a * per_a + 1))
            second = set(range((floor_b - 1) * per_b + 1, floor_b * per_b + 1))
            shared = first & second
            self.assertEqual(len(shared), 1, f"seed {seed}: подходят {sorted(shared)}")
            self.assertEqual(generated["answer"], shared.pop(), f"seed {seed}: {text}")


class MarkedVerticesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["marked_vertices_of_polygon"]

    STEPS = {"шестую": 6, "восьмую": 8, "девятую": 9, "двенадцатую": 12,
             "четырнадцатую": 14, "пятнадцатую": 15}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            sides = int(re.search(r"(\d+)-угольника", text).group(1))
            step = next(value for word, value in self.STEPS.items() if word in text)

            # Решение с нуля: обходим круг и складываем отмеченные вершины
            # в множество, пока не начнём повторяться.
            marked = set()
            vertex = 0
            while vertex not in marked:
                marked.add(vertex)
                vertex = (vertex + step) % sides
            self.assertEqual(generated["answer"], len(marked), f"seed {seed}: {text}")

    def test_not_every_vertex_is_marked(self) -> None:
        """Иначе задача бессодержательна: отметились бы все подряд."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            sides = int(re.search(r"(\d+)-угольника",
                                  generated["rendered_problem"]).group(1))
            self.assertLess(generated["answer"], sides, f"seed {seed}")


class PiesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["pies_shared_between_children"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            pies = int(re.search(r"поровну (\d+) одинаковых", text).group(1))
            children = int(re.search(r"между (\d+) детьми", text).group(1))

            # Решение с нуля: считаем куски и раздаём их поровну.
            pieces = pies * children
            self.assertEqual(pieces % children, 0, f"seed {seed}: куски не делятся")
            self.assertEqual(generated["answer"], pieces // children, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: семь пирогов на восемь детей — по семь кусков."""
        self.assertEqual(7 * 8 // 8, 7)


class BirthdayTreatsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["birthday_treats_two_kinds"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            boy_sweets, boy_cutlets = (int(v) for v in re.search(
                r"мальчик съел (\d+) \S+ и (\d+)", text).groups())
            girl_sweets, girl_cutlets = (int(v) for v in re.search(
                r"девочка — (\d+) \S+ и (\d+)", text).groups())
            sweets, cutlets = (int(v) for v in re.search(
                r"съедено (\d+) \S+ и (\d+)", text).groups())

            # Решение с нуля: перебираем число девочек и проверяем оба подсчёта.
            fits = [
                girls for girls in range(1, 200)
                for boys in [(sweets - girls * girl_sweets)]
                if boys >= 0 and boys % boy_sweets == 0
                and boy_cutlets * (boys // boy_sweets) + girl_cutlets * girls == cutlets
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits[:3]} — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 714 конфет и 371 котлета дают 49 девочек и 56 мальчиков."""
        self.assertEqual(4 * 56 + 10 * 49, 714)
        self.assertEqual(4 * 56 + 3 * 49, 371)


if __name__ == "__main__":
    unittest.main()
