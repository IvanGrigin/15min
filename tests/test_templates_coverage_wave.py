"""Независимая проверка волны покрытия: прямоугольник, лист, деньги, мост.

Тест решает задачу заново по напечатанному тексту и другим способом.
Прямоугольник шаблон строит по готовой формуле — тест ищет стороны перебором.
Мост шаблон считает вперёд — тест идёт с конца, как ребёнок. Лист железа
шаблон собирает из веса квадратного сантиметра — тест делит и умножает
как в условии.
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


class RectangleExcessTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rectangle_perimeter_exceeds_area"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            excess = int(re.search(r"на (\d+) больше площади", text).group(1))
            sides = [int(value) for value in re.findall(r"(\d+) сантиметр", generated["answer_text"])]
            self.assertEqual(len(sides), 2, f"seed {seed}: {generated['answer_text']}")
            long_side, short_side = sides

            # Напечатанный ответ обязан удовлетворять условию.
            self.assertEqual(2 * (long_side + short_side) - long_side * short_side, excess,
                             f"seed {seed}: {text}")

            # Решение с нуля: перебираем меньшую сторону. Задача обещает
            # «пример», и тест проверяет, что пример на самом деле один.
            fits = []
            for small in range(1, 40):
                # 2a + 2b = ab + k при известном b даёт a(2 − b) = k − 2b.
                if small == 2:
                    continue
                numerator = excess - 2 * small
                denominator = 2 - small
                if numerator % denominator == 0:
                    big = numerator // denominator
                    if big >= small:
                        fits.append((big, small))
            self.assertEqual(fits, [(long_side, short_side)],
                             f"seed {seed}: подходят {fits} — {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: разность 2023 даёт стороны 2021 и 1."""
        self.assertEqual(2 * (2021 + 1) - 2021 * 1, 2023)


class SheetWeightTests(unittest.TestCase):
    TEMPLATE = LIBRARY["sheet_weight_scaling"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            width, height = (int(v) for v in re.search(
                r"размерами (\d+) см × (\d+) см", text).groups())
            weight = int(re.search(r"весит (\d+)", text).group(1))
            count = int(re.search(r"весят (\d+) квадратных", text).group(1))
            side = 100 if "квадратных метров" in text else 10

            # Решение с нуля: вес квадратного сантиметра, затем нужная площадь.
            per_cm = weight / (width * height)
            expected = per_cm * count * side * side
            self.assertEqual(expected, int(expected), f"seed {seed}: не целый ответ")
            self.assertEqual(generated["answer"], int(expected), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 21 × 30 см весят 1800 г, значит 7 м² — 200 000 г."""
        self.assertEqual(1800 / (21 * 30) * 7 * 10000, 200000)


class MoneyEqualizeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["money_equalize_pair"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            answer = int(re.search(r"(\d+)", generated["answer_text"]).group(1))

            if "поровну" in text:
                gap = int(re.search(r"на\s(\d+)\s?\S+\sменьше", text).group(1))
                # Решение с нуля: у обоих было по 100; проверяем передачу.
                start = 100
                self.assertEqual((start + answer) - (start - answer), gap,
                                 f"seed {seed}: {text}")
            else:
                total = int(re.search(r"собой\s(\d+)\s?", text).group(1))
                gap = int(re.search(r"на\s(\d+)\s?\S+\sбольше", text).group(1))
                # Ответ — меньшая доля; вторая доля восстанавливается по разнице.
                self.assertEqual(answer + (answer + gap), total, f"seed {seed}: {text}")

    def test_both_shells_occur(self) -> None:
        seen = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add("поровну" in text)
        self.assertEqual(seen, {True, False})

    def test_source_example_reproduces(self) -> None:
        """Контроль: разница 12 достигается передачей 6 рублей."""
        self.assertEqual((100 + 6) - (100 - 6), 12)


class DoublingBridgeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["doubling_bridge_toll"]

    WORDS = {"Дважды": 2, "Трижды": 3, "Четырежды": 4}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            toll = int(re.search(r"мост, (\d+) рубл", text).group(1))
            crossings = next(count for word, count in self.WORDS.items() if word in text)
            answer = int(re.match(r"(\d+)", generated["answer_text"]).group(1))

            # Решение с нуля: идём вперёд от найденного ответа и проверяем ноль.
            money = answer
            for _ in range(crossings):
                money = money * 2 - toll
            self.assertEqual(money, 0, f"seed {seed}: {text}")

            # И с конца — тем способом, каким задачу решают дети.
            backwards = 0
            for _ in range(crossings):
                backwards = (backwards + toll) / 2
            self.assertEqual(backwards, answer, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: три перехода с пошлиной 40 обнуляют 35 рублей."""
        money = 35
        for _ in range(3):
            money = money * 2 - 40
        self.assertEqual(money, 0)


if __name__ == "__main__":
    unittest.main()

