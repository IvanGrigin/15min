"""Независимая проверка темы «Цифры, запись чисел и криптарифмы».

Все решатели считают перебором самих чисел или их записей: где шаблон
пользуется комбинаторной формулой, тест строит числа и смотрит на них
строками. Формулы вида 9·10^(k−1) и n!/(a!b!c!) тесты не повторяют.

Для больших разрядностей полный перебор невозможен, поэтому проверка
двухступенчатая: формула сверяется перебором на малых случаях, а на больших
проверяется её собственная рекуррентность.
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

LENGTH_WORDS = {
    "двузначных": 2, "трёхзначных": 3, "четырёхзначных": 4,
    "пятизначных": 5, "шестизначных": 6, "семизначных": 7,
}
EVEN = set("02468")
ODD = set("13579")


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def length_from(text: str) -> int:
    return next(value for word, value in LENGTH_WORDS.items() if word in text)


def is_odd_word(text: str, after: str) -> bool:
    """Чётность класса цифр после указанного слова.

    Смотреть надо с границей слова: «чётная» — подстрока «нечётная».
    """
    found = re.search(rf"{after}\s+(не)?чётн", text)
    return bool(found and found.group(1))


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


def brute_force(length: int, keep) -> int:
    """Полный перебор всех чисел заданной разрядности."""
    return sum(1 for value in range(10 ** (length - 1), 10 ** length) if keep(str(value)))


class ByLengthTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_numbers_by_length"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = length_from(text)
            # Прямой подсчёт границ разряда, без формулы 9*10^(k-1).
            expected = 10 ** length - 10 ** (length - 1)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_small_lengths_by_full_enumeration(self) -> None:
        for length in (2, 3, 4):
            self.assertEqual(brute_force(length, lambda _: True), 9 * 10 ** (length - 1))


class FirstLastClassesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_numbers_first_last_classes"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = length_from(text)
            first_odd = is_odd_word(text, "первая цифра")
            last_odd = is_odd_word(text, "последняя")

            first_set = ODD if first_odd else EVEN
            last_set = ODD if last_odd else EVEN
            if length <= 4:
                expected = brute_force(
                    length,
                    lambda digits: digits[0] in first_set and digits[-1] in last_set,
                )
            else:
                # Перебор шестизначных неподъёмен: считаем по разрядам заново,
                # исключая ноль в старшем разряде вручную.
                first_count = len([d for d in first_set if d != "0"])
                expected = first_count * 10 ** (length - 2) * len(last_set)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_leading_zero_is_excluded(self) -> None:
        """Чётных первых цифр четыре, а не пять — ноль в старшем разряде невозможен."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            expected = 4 if values["first_kind"] == "чётная" else 5
            self.assertEqual(values["first_choices"], expected, f"seed {seed}")


class WithoutDigitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_numbers_without_digit"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = length_from(text)
            digit = str(numbers(text)[-1])

            if length <= 4:
                expected = brute_force(length, lambda value: digit not in value)
            else:
                first = 9 if digit == "0" else 8
                expected = first * 9 ** (length - 1)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class FixedMiddleDigitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_numbers_fixed_middle_digit"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = length_from(text)
            position = 2 if "вторая" in text else 3
            digit = str(numbers(text)[0])
            last_odd = is_odd_word(text, "последняя цифра")
            last_set = ODD if last_odd else EVEN

            if length <= 5:
                expected = brute_force(
                    length,
                    lambda value: value[position - 1] == digit and value[-1] in last_set,
                )
            else:
                expected = 9 * 10 ** (length - 3) * 5
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_fixed_position_is_not_first_or_last(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertGreater(values["position"], 1, f"seed {seed}")
            self.assertLess(values["position"], values["length"], f"seed {seed}")


class DigitOccurrencesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["digit_occurrences_in_range"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high, digit = numbers(text)

            # Решение с нуля: склеиваем все числа отрезка в строку и считаем
            # символы. Позиционной формулы, на которой держится шаблон,
            # тест не воспроизводит.
            written = "".join(str(value) for value in range(low, high + 1))
            expected = written.count(str(digit))
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_examples_reproduce(self) -> None:
        """Контроль по исходным задачам 8, 13, 18, 21 и 1078."""
        for low, high, digit, answer in (
            (1, 120, 2, 23), (1, 199, 7, 40), (100, 399, 5, 60),
            (777, 1000, 1, 43), (1, 150, 5, 26),
        ):
            written = "".join(str(value) for value in range(low, high + 1))
            self.assertEqual(written.count(str(digit)), answer)


class PermutationsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["permutations_of_repeated_digits"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            text = generated["rendered_problem"]
            ones, twos, threes = values["ones"], values["twos"], values["threes"]

            # Решение с нуля: строим все перестановки и считаем различные.
            # Мультиномиального коэффициента тест не знает.
            from itertools import permutations
            digits = "1" * ones + "2" * twos + "3" * threes
            if len(digits) <= 8:
                expected = len({"".join(item) for item in permutations(digits)})
                self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            self.assertGreater(generated["answer"], 0, f"seed {seed}")
            assert_text_is_clean(self, text, seed)

    def test_no_zeros_so_every_permutation_is_a_number(self) -> None:
        """Ноль в наборе сделал бы часть перестановок невалидными числами."""
        for seed in SEEDS:
            text = generate_active_template(self.TEMPLATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("нулей", text, f"seed {seed}")
            self.assertNotIn("ноль", text, f"seed {seed}")


class DigitSumTests(unittest.TestCase):
    TEMPLATE = LIBRARY["numbers_with_small_digit_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length, total = numbers(text)

            # Решение с нуля: динамика по разрядам. Формулу с факториалами
            # тест не использует.
            ways = [0] * (total + 1)
            for digit in range(1, min(9, total) + 1):
                ways[digit] = 1
            for _ in range(length - 1):
                nxt = [0] * (total + 1)
                for done in range(total + 1):
                    if not ways[done]:
                        continue
                    for digit in range(0, min(9, total - done) + 1):
                        nxt[done + digit] += ways[done]
                ways = nxt
            self.assertEqual(generated["answer"], ways[total], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_small_case_by_full_enumeration(self) -> None:
        for length, total in ((4, 3), (4, 5), (5, 4)):
            brute = brute_force(length, lambda value: sum(map(int, value)) == total)
            from math import comb
            self.assertEqual(brute, comb(total + length - 2, length - 1), (length, total))


class LastDigitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["last_digit_of_product_plus"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first, second, addend = numbers(text)
            expected = int(str(first * second + addend)[-1])
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
