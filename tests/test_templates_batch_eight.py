"""Независимая проверка задачи о вычёркивании последней цифры.

Тест перебирает все четырёхзначные числа нужной чётности и проверяет,
что напечатанное — действительно наибольшее подходящее.
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


class FourDigitHeadPlusLastTests(unittest.TestCase):
    TEMPLATE = LIBRARY["four_digit_head_plus_last"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"Вышло (\d+)", text).group(1))
            wants_odd = "нечётного" in text

            # Решение с нуля: перебираем все четырёхзначные числа.
            fits = [
                number for number in range(1000, 10000)
                if (number % 2 == 1) == wants_odd
                and number // 10 + number % 10 == total
            ]
            self.assertTrue(fits, f"seed {seed}: ни одного числа — {text}")
            self.assertEqual(generated["answer"], max(fits), f"seed {seed}: {text}")

    def test_several_numbers_fit(self) -> None:
        """Задача просит наибольшее не зря: подходящих чисел всегда несколько."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"Вышло (\d+)", text).group(1))
            wants_odd = "нечётного" in text
            fits = [
                number for number in range(1000, 10000)
                if (number % 2 == 1) == wants_odd
                and number // 10 + number % 10 == total
            ]
            self.assertGreater(len(fits), 1, f"seed {seed}: ответ и так один — {text}")


if __name__ == "__main__":
    unittest.main()
