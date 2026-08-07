"""Независимая проверка приёмов «числа с общей частью».

Два шаблона первого батча по каталогу `docs/UNCOVERED_BY_TECHNIQUE.md`:
набор чисел, отличающихся ровно одной цифрой, и суммы чисел по последней
цифре. Оба приёма в библиотеке отсутствовали.

Решатели устроены иначе, чем шаблоны. Шаблон находит набор делением суммы
на общую часть и цифры; тест перебирает все наборы подряд и требует, чтобы
подходил ровно один — источник просит «придумайте», и ценность ключа
именно в том, что придумать можно только одно. Суммы по последней цифре
шаблон считает формулой прогрессии, а тест складывает числа по одному.
"""
from __future__ import annotations

import itertools
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
SEEDS = range(30)


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class DifferInOneDigitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["numbers_differing_in_one_digit"]

    COUNTS = {"три": 3, "четыре": 4}
    LENGTHS = {"трёхзначных": 3, "четырёхзначных": 4}

    @classmethod
    def read_condition(cls, text: str) -> tuple[int, int, str, int]:
        count = next(value for word, value in cls.COUNTS.items() if f"{word} различных" in text)
        length = next(value for word, value in cls.LENGTHS.items() if word in text)
        position = "first" if "первой цифрой" in text else "last"
        total = numbers(text)[0]
        return count, length, position, total

    @staticmethod
    def brute_force(count: int, length: int, position: str, total: int) -> list[list[int]]:
        """Перебор всех наборов подряд, без разложения суммы на части."""
        found = []
        if position == "first":
            step = 10 ** (length - 1)
            for digits in itertools.combinations(range(1, 10), count):
                for common in range(step):
                    group = [digit * step + common for digit in digits]
                    if sum(group) == total:
                        found.append(sorted(group))
        else:
            low, high = 10 ** (length - 2), 10 ** (length - 1)
            for digits in itertools.combinations(range(10), count):
                for common in range(low, high):
                    group = [common * 10 + digit for digit in digits]
                    if sum(group) == total:
                        found.append(sorted(group))
        return sorted(found)

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count, length, position, total = self.read_condition(text)
            found = self.brute_force(count, length, position, total)

            self.assertEqual(len(found), 1, f"seed {seed}: наборов не один — {text}")
            group = found[0]
            if "наибольшее из них" in text:
                expected = str(group[-1])
            elif "общую часть" in text:
                expected = str(
                    group[0] % 10 ** (length - 1) if position == "first" else group[0] // 10
                )
            else:
                expected = ", ".join(str(value) for value in group)
            self.assertEqual(str(generated["answer"]), expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_numbers_really_differ_in_one_digit(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count, length, position, total = self.read_condition(text)
            group = self.brute_force(count, length, position, total)[0]

            written = [str(value) for value in group]
            self.assertTrue(all(len(item) == length for item in written), f"seed {seed}")
            differing = [
                index for index in range(length)
                if len({item[index] for item in written}) > 1
            ]
            place = 0 if position == "first" else length - 1
            self.assertEqual(differing, [place], f"seed {seed}: {written}")
            self.assertEqual(len(set(group)), count, f"seed {seed}: числа обязаны быть разными")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику: сумма 817 -> 139, 239, 439 и ничего больше."""
        self.assertEqual(self.brute_force(3, 3, "first", 817), [[139, 239, 439]])


class SumByLastDigitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["sum_of_numbers_by_last_digit"]

    LENGTHS = {"трёхзначн": 3, "четырёхзначн": 4}

    @staticmethod
    def numbers_ending_with(length: int, digit: int) -> list[int]:
        low, high = 10 ** (length - 1), 10 ** length
        return [value for value in range(low, high) if value % 10 == digit]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = next(value for word, value in self.LENGTHS.items() if word in text)
            printed = numbers(text)

            # Числа складываются по одному: формулой прогрессии тест
            # не пользуется, иначе он повторял бы шаблон.
            if "На сколько сумма" in text:
                first, second = printed[0], printed[1]
                expected = (
                    sum(self.numbers_ending_with(length, first))
                    - sum(self.numbers_ending_with(length, second))
                )
            elif "Сколько всего" in text:
                expected = len(self.numbers_ending_with(length, printed[0]))
            else:
                expected = sum(self.numbers_ending_with(length, printed[0]))

            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_count_does_not_depend_on_the_digit(self) -> None:
        """На этом и стоит задача: голов поровну у любой последней цифры."""
        for length in (3, 4):
            sizes = {len(self.numbers_ending_with(length, digit)) for digit in range(10)}
            self.assertEqual(len(sizes), 1, f"{length}-значные: {sizes}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 302: девятка против двойки — разность 630."""
        nines = sum(self.numbers_ending_with(3, 9))
        twos = sum(self.numbers_ending_with(3, 2))
        self.assertEqual(nines - twos, 630)
        self.assertEqual(len(self.numbers_ending_with(3, 9)), 90)


if __name__ == "__main__":
    unittest.main()
