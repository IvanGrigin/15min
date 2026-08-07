"""Независимо проверяет JSON-шаблоны темы «Множители и факториалы»."""
from __future__ import annotations

import math
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


def number_values(text: str) -> list[int]:
    """Возвращает все целые числа, напечатанные в условии."""
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    """Проверяет, что условие полностью отрендерено."""
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class FactorPairMinimumTests(unittest.TestCase):
    """Перебирает пары делителей вместо использования формулы шаблона."""

    def test_matches_divisor_enumeration(self) -> None:
        """Находит минимум среди пар, отвечающих напечатанному ограничению."""
        template = LIBRARY["factor_pair_min_sum"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            text = generated["rendered_problem"]
            target = number_values(text)[0]
            candidates = []
            for first in range(1, math.isqrt(target) + 1):
                if target % first:
                    continue
                second = target // first
                if "двух чётных" in text and (first % 2 or second % 2):
                    continue
                if "двух нечётных" in text and (first % 2 == 0 or second % 2 == 0):
                    continue
                if "хотя бы один из которых нечётный" in text and first % 2 == 0 and second % 2 == 0:
                    continue
                if "нет ни одной цифры 0" in text and ("0" in str(first) or "0" in str(second)):
                    continue
                if "полный квадрат" in text and not any(
                    math.isqrt(value) ** 2 == value for value in (first, second)
                ):
                    continue
                candidates.append(first + second)
            self.assertTrue(candidates, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], min(candidates), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_condition_actually_changes_the_answer(self) -> None:
        """Иначе задача сводится к извлечению корня, и условие декоративно.

        Прежняя версия шаблона строила число как root² и печатала 2·root:
        ограничение на множители ни на что не влияло. Замечено преподавателем.
        """
        template = LIBRARY["factor_pair_min_sum"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            target = number_values(generated["rendered_problem"])[0]

            # Пара, ближайшая к корню, — это минимум суммы вообще без условий.
            closest = max(
                (first, target // first)
                for first in range(1, math.isqrt(target) + 1) if target % first == 0)
            self.assertNotEqual(
                generated["answer"], closest[0] + closest[1],
                f"seed {seed}: условие не влияет на ответ — {generated['rendered_problem']}")


class TrailingZerosTests(unittest.TestCase):
    """Проверяет нули непосредственным умножением всех множителей."""

    def test_matches_direct_product(self) -> None:
        """Строит произведение буквально по границам, напечатанным в условии."""
        template = LIBRARY["trailing_zeros_consecutive_product"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            text = generated["rendered_problem"]
            start, next_value, end = number_values(text)
            self.assertEqual(next_value, start + 1, f"seed {seed}: {text}")
            product = math.prod(range(start, end + 1))
            expected = len(str(product)) - len(str(product).rstrip("0"))
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class FactorPairWithoutZeroTests(unittest.TestCase):
    """Перебирает делители, чья десятичная запись не содержит нуля."""

    def test_matches_admissible_divisor_enumeration(self) -> None:
        """Ищет минимум без опоры на неравенство из шаблона."""
        template = LIBRARY["factor_pair_min_sum_without_zero_digits"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            text = generated["rendered_problem"]
            target = number_values(text)[0]
            candidates = []
            for first in range(1, math.isqrt(target) + 1):
                if target % first:
                    continue
                second = target // first
                if "0" not in str(first) and "0" not in str(second):
                    candidates.append(first + second)
            self.assertTrue(candidates, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], min(candidates), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
