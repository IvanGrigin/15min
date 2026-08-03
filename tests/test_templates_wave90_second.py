"""Независимая проверка второй волны плана на 90%.

Арбуз, мост, перевод квадратных единиц, ряд коробок и наименьшая группа.
Тест каждый раз идёт не тем путём, каким считает шаблон: сухую часть арбуза
он проверяет с обеих сторон, длину моста восстанавливает из долей, ряд
коробок складывает подряд, а наименьшую группу ищет перебором снизу.
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


class WatermelonDryingTests(unittest.TestCase):
    TEMPLATE = LIBRARY["watermelon_drying_percent"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            fresh = int(re.search(r"весил (\d+)", text).group(1))
            wet, dry = (int(v) for v in re.findall(r"(\d+)%", text))
            answer = generated["answer"]

            # Решение с нуля: сухая часть не испаряется, значит её вес
            # одинаков до и после. Считаем его с обеих сторон.
            solid_before = Fraction(fresh) * Fraction(100 - wet, 100)
            solid_after = Fraction(answer) * Fraction(100 - dry, 100)
            self.assertEqual(solid_before, solid_after, f"seed {seed}: {text}")
            self.assertLess(answer, fresh, f"seed {seed}: подсохший стал тяжелее")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 10 кг при 99% воды после подсыхания до 98% — это 5 кг."""
        self.assertEqual(Fraction(10) * Fraction(1, 100), Fraction(5) * Fraction(2, 100))


class BridgeLengthTests(unittest.TestCase):
    TEMPLATE = LIBRARY["bridge_over_river_length"]

    PARTS = {"четверть": 4, "пятая часть": 5, "шестая часть": 6,
             "восьмая часть": 8, "десятая часть": 10}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            river = int(re.search(r"шириной (\d+)", text).group(1))
            denominator = next(d for word, d in self.PARTS.items() if word in text)
            answer = generated["answer"]

            # Решение с нуля: над водой висит то, что осталось после берегов.
            over_water = Fraction(answer) * (1 - Fraction(2, denominator))
            self.assertEqual(over_water, river, f"seed {seed}: {text}")
            self.assertGreater(answer, river, f"seed {seed}: мост короче реки")

    def test_source_example_reproduces(self) -> None:
        """Контроль: по пятой части на берег и река 120 метров — мост 200."""
        self.assertEqual(200 * (1 - Fraction(2, 5)), 120)


class SquareUnitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_units_conversion"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            ratio = int(re.search(r"— (\d+) ", text).group(1))
            count = int(re.search(r"в (\d+) квадратных", text).group(1))

            # Решение с нуля: выкладываем квадрат стороной ratio маленькими
            # квадратиками — их ровно ratio строк по ratio штук.
            in_one = sum(ratio for _ in range(ratio))
            self.assertEqual(generated["answer"], count * in_one, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: в трёх квадратных футах 432 квадратных дюйма."""
        self.assertEqual(3 * 12 * 12, 432)


class BoxesRowTests(unittest.TestCase):
    TEMPLATE = LIBRARY["boxes_growing_row_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            extra = int(re.search(r"на (\d+) больше", text).group(1))
            full = int(re.search(r"было бы всего (\d+)", text).group(1))

            # Решение с нуля: складываем подряд, пока не наберём обещанную
            # сумму. Так находится, сколько коробок было бы.
            running = 0
            grown = 0
            while running < full:
                grown += 1
                running += grown
            self.assertEqual(running, full, f"seed {seed}: сумма недостижима — {text}")

            boxes = grown - extra
            self.assertEqual(generated["answer"], boxes * (boxes + 1) // 2,
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 5050 — сумма до ста; при 97 коробках выходит 4753."""
        self.assertEqual(100 * 101 // 2, 5050)
        self.assertEqual(97 * 98 // 2, 4753)


class MinimalGroupTests(unittest.TestCase):
    TEMPLATE = LIBRARY["minimal_group_by_percent"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            percent = int(re.search(r"больше (\d+)%", text).group(1))

            # Решение с нуля: перебираем размер группы снизу и ищем первый,
            # при котором большинство может превысить порог, а меньшинство
            # остаётся непустым.
            fits = next(
                total for total in range(2, 500)
                if any(Fraction(major, total) * 100 > percent
                       for major in range(1, total))
            )
            self.assertEqual(generated["answer"], fits, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: при 94% наименьшая группа — 17 человек."""
        self.assertGreater(Fraction(16, 17) * 100, 94)
        self.assertLessEqual(Fraction(15, 16) * 100, 94)


if __name__ == "__main__":
    unittest.main()
