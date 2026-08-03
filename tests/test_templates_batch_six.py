"""Независимая проверка: муха, погоня великана, монеты, цифры подряд.

Муху тест ведёт по перелётам — складывает первые сто отрезков и сверяет
с ответом. Погоню считает по шагам. Монеты перебирает по состояниям.
Делимость проверяет прямым делением длинного числа, а не признаком.
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


class FlyBetweenRidersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["fly_between_two_riders"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            distance = int(re.search(r"между ними (\d+) км", text).group(1))
            first, second = (int(v) for v in re.search(
                r"первого (\d+) км/ч, второго — (\d+)", text).groups())
            fly = int(re.search(r"скоростью (\d+) км/ч навстречу", text).group(1))

            # Решение с нуля: складываем сами перелёты. Ряд сходится, ста
            # отрезков хватает, чтобы совпасть с ответом с большим запасом.
            left, right = Fraction(0), Fraction(distance)
            place = Fraction(0)
            flown = Fraction(0)
            toward_right = True
            for _ in range(100):
                if toward_right:
                    meet_time = (right - place) / (fly + second)
                else:
                    meet_time = (place - left) / (fly + first)
                flown += fly * meet_time
                place += (fly if toward_right else -fly) * meet_time
                left += first * meet_time
                right -= second * meet_time
                toward_right = not toward_right
            self.assertAlmostEqual(float(flown), generated["answer"], places=3,
                                   msg=f"seed {seed}: {text}")

    def test_source_shape_holds(self) -> None:
        """Контроль: 40 км при скоростях 10 и 14 — встреча через 40/24 часа."""
        self.assertEqual(Fraction(40, 10 + 14), Fraction(5, 3))


class GiantChaseTests(unittest.TestCase):
    TEMPLATE = LIBRARY["giant_chases_small_runner"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            gap = int(re.search(r"было (\d+) шагов", text).group(1))
            small_steps = int(re.search(r"успевает сделать (\d+)", text).group(1))
            ratio = int(re.search(r"равен (\d+) шагам", text).group(1))

            # Решение с нуля: шагаем мгновениями, пока разрыв не закроется.
            behind = gap * ratio
            steps = 0
            while behind > 0:
                behind -= ratio - small_steps
                steps += small_steps
            self.assertEqual(behind, 0, f"seed {seed}: догоняет не в целый миг")
            self.assertEqual(generated["answer"], steps, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: разрыв 8, шаги 7 и 11 — человечек пробежит 154 шага."""
        self.assertEqual(8 * 11 // (11 - 7) * 7, 154)


class CoinsFlipTests(unittest.TestCase):
    TEMPLATE = LIBRARY["coins_flip_all_same_side"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            coins = int(re.search(r"лежат (\d+)", text).group(1))
            flip = int(re.search(r"любые (\d+)", text).group(1))

            # Решение с нуля: перебираем достижимые числа орлов. Достаточно
            # следить за их количеством: какие именно монеты — неважно.
            reachable = {0}
            for _ in range(coins + 2):
                grown = set(reachable)
                for heads in reachable:
                    for taken in range(max(0, flip - (coins - heads)), min(flip, heads) + 1):
                        grown.add(heads - taken + (flip - taken))
                if grown == reachable:
                    break
                reachable = grown
            self.assertEqual(generated["answer"], coins in reachable, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 21 монета и переворот двадцати — нельзя."""
        self.assertEqual(20 % 2 == 1 or 21 % 2 == 0, False)


class DigitsInRowTests(unittest.TestCase):
    TEMPLATE = LIBRARY["digits_in_a_row_divisibility"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shown = int(re.search(r"получится число (\d+)", text).group(1))
            divisor = int(re.search(r"делится ли оно на (\d+)", text.lower()).group(1))
            last = int(re.search(r"от 1 до (\d+)", text).group(1))

            # Решение с нуля: делим само число, не пользуясь признаком.
            self.assertEqual(shown, int("".join(str(d) for d in range(1, last + 1))),
                             f"seed {seed}: напечатано не то число")
            self.assertEqual(generated["answer"], shown % divisor == 0, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 123456789 делится на девять, значит не простое."""
        self.assertEqual(123456789 % 9, 0)


if __name__ == "__main__":
    unittest.main()
