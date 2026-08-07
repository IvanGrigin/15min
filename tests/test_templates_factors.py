"""Независимо проверяет JSON-шаблоны темы «Множители и факториалы»."""
from __future__ import annotations

import itertools
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


class SumWithTrailingZerosTests(unittest.TestCase):
    """Набор чисел проверяется по свойству, а не по совпадению с ключом.

    Верных наборов много, и ключ печатает один как пример. Поэтому решатель
    здесь делает две разные вещи: убеждается, что напечатанный пример
    действительно годится, и отдельно ищет свой собственный набор перебором —
    иначе задача могла бы оказаться неразрешимой ни для кого, кроме шаблона.
    """

    TEMPLATE = LIBRARY["numbers_with_sum_and_zero_product"]
    COUNT_WORDS = {"три": 3, "четыре": 4}
    ZERO_WORDS = {
        "тремя": 3, "четырьмя": 4, "пятью": 5, "шестью": 6,
    }

    @staticmethod
    def zeros_of(numbers: list[int]) -> int:
        """Нули считаются умножением честно, а не через двойки и пятёрки."""
        product = 1
        for value in numbers:
            product *= value
        text = str(product)
        return len(text) - len(text.rstrip("0"))

    def test_printed_example_is_valid(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = next(value for word, value in self.COUNT_WORDS.items() if word in text)
            zeros = next(value for word, value in self.ZERO_WORDS.items() if word in text)
            total = number_values(text)[0]

            example = [int(part) for part in generated["answer"].split(",")]
            self.assertEqual(len(example), count, f"seed {seed}: {text}")
            self.assertEqual(sum(example), total, f"seed {seed}: {text}")
            self.assertGreaterEqual(self.zeros_of(example), zeros, f"seed {seed}: {text}")
            self.assertTrue(all(value >= 2 for value in example), f"seed {seed}: {example}")
            assert_text_is_clean(self, text, seed)

    def test_child_can_find_some_answer(self) -> None:
        """Свой набор, найденный независимо: задача обязана быть разрешимой."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = next(value for word, value in self.COUNT_WORDS.items() if word in text)
            zeros = next(value for word, value in self.ZERO_WORDS.items() if word in text)
            total = number_values(text)[0]

            # Перебор по числам вида 2^a·5^b: их немного, и именно из них
            # состоят решения корпуса.
            pool = sorted({
                2 ** a * 5 ** b
                for a in range(0, 9) for b in range(0, 5)
                if 2 <= 2 ** a * 5 ** b <= total
            })
            found = None
            for combo in itertools.combinations_with_replacement(pool, count):
                if sum(combo) == total and self.zeros_of(list(combo)) >= zeros:
                    found = combo
                    break
            self.assertIsNotNone(found, f"seed {seed}: решения не существует — {text}")

    def test_key_says_the_answer_is_an_example(self) -> None:
        """Ключ обязан признаваться, что верных ответов много."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            rendered = generated["answer_text"]
            self.assertIn("например", rendered, f"seed {seed}: {rendered}")
            self.assertIn("любой набор", rendered, f"seed {seed}: {rendered}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 342: 50 + 8 + 25 = 83, четыре нуля."""
        self.assertEqual(50 + 8 + 25, 83)
        self.assertEqual(self.zeros_of([50, 8, 25]), 4)


if __name__ == "__main__":
    unittest.main()
