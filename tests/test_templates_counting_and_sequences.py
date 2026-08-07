"""Независимая проверка тем «Промежутки», «Делимость», «Цифры» и «Прогрессии».

Все решатели здесь работают перебором: честно пробегают отрезок числами
и считают подходящие. Ровно на этом и ловятся ошибки в границах — главная
трудность этих тем. Формулы с целочисленным делением тесты не повторяют.
"""
from __future__ import annotations

import functools
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
SPACE = r"[\s ]+"


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class ParityInRangeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_parity_in_range"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high = numbers(text)
            wanted = 1 if "нечётные" in text else 0

            # Решение с нуля: пробегаем отрезок и считаем. Целочисленного
            # деления, на котором держится шаблон, тест не использует.
            expected = sum(1 for value in range(low, high + 1) if value % 2 == wanted)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_both_bounds_are_included(self) -> None:
        """Границы входят в отрезок — на этом ошибаются чаще всего."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            low, high = values["low"], values["high"]
            wanted = 1 if values["parity"] == "нечётные" else 0
            inside = sum(1 for value in range(low, high + 1) if value % 2 == wanted)
            self.assertEqual(values["count"], inside, f"seed {seed}")


class StrictlyBetweenTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_integers_strictly_between"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high = numbers(text)
            expected = len(range(low + 1, high))
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class MultiplesInRangeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_multiples_in_range"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high, divisor = numbers(text)
            inclusive = "включительно" in text

            span = range(low, high + 1) if inclusive else range(low + 1, high)
            expected = sum(1 for value in span if value % divisor == 0)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_both_kinds_of_bounds_appear(self) -> None:
        kinds = {
            generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]["kind"]
            for seed in range(60)
        }
        self.assertEqual(kinds, {"включительно", "строго"})


class EvenMultiplesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_even_multiples_in_range"]

    SELECTORS = {
        "которые чётны": lambda value: value % 2 == 0,
        "которые нечётны": lambda value: value % 2 == 1,
        "которые оканчиваются на 5": lambda value: value % 10 == 5,
        "которые оканчиваются на 0": lambda value: value % 10 == 0,
    }

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # Чисел в условии бывает четыре: «оканчиваются на 5» добавляет
            # своё. Берём по смыслу, а не по порядку.
            low, high = (int(v) for v in re.search(r"от (\d+) до (\d+)", text).groups())
            divisor = int(re.search(r"делится на (\d+)", text).group(1))
            keep = next(rule for phrase, rule in self.SELECTORS.items() if phrase in text)

            # Решение с нуля: перебор с двумя условиями сразу.
            expected = sum(
                1 for value in range(low, high + 1)
                if keep(value) and value % divisor == 0
            )
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_selection_is_not_redundant(self) -> None:
        """Отбор обязан сужать: иначе условие в задаче лишнее.

        При чётном делителе слово «чётных» ничего не добавляет, а числа,
        оканчивающиеся на 0, и так все делятся на 5.
        """
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high = (int(v) for v in re.search(r"от (\d+) до (\d+)", text).groups())
            divisor = int(re.search(r"делится на (\d+)", text).group(1))
            without = sum(1 for value in range(low, high + 1) if value % divisor == 0)
            self.assertLess(generated["answer"], without, f"seed {seed}: {text}")

    def test_all_four_selections_occur(self) -> None:
        seen = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add(next(p for p in self.SELECTORS if p in text))
        self.assertEqual(seen, set(self.SELECTORS), "выпадают не все виды отбора")


class DigitsFromOneSetTests(unittest.TestCase):
    TEMPLATE = LIBRARY["digits_all_from_one_set"]

    WORDS = {"трёхзначных": 3, "четырёхзначных": 4, "пятизначных": 5, "шестизначных": 6}
    SETS = {
        "чётные": {0, 2, 4, 6, 8},
        "нечётные": {1, 3, 5, 7, 9},
        "делятся на 3": {0, 3, 6, 9},
    }

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = next(value for word, value in self.WORDS.items() if word in text)
            # Граница слова обязательна: «чётные» — подстрока «нечётные».
            digits = next(
                value for word, value in self.SETS.items()
                if re.search(rf"(?<![а-яё]){word}", text)
            )

            # Решение с нуля: считаем варианты по разрядам, отдельно первый.
            # Формулу вида 4*5^(k-1) тест не воспроизводит — он строит её заново
            # из самого множества цифр.
            first = len([digit for digit in digits if digit != 0])
            expected = first * len(digits) ** (length - 1)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_small_case_by_full_enumeration(self) -> None:
        """Трёхзначный случай проверяется полным перебором всех чисел."""
        for name, digits in self.SETS.items():
            brute = sum(
                1 for value in range(100, 1000)
                if all(int(char) in digits for char in str(value))
            )
            first = len([digit for digit in digits if digit != 0])
            self.assertEqual(brute, first * len(digits) ** 2, name)


class RemainderTests(unittest.TestCase):
    TEMPLATE = LIBRARY["remainder_by_two_signs"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # Признаки делимости из условия убраны: ребёнок должен сам
            # сообразить, на какие взаимно простые множители разложить делитель.
            number, divisor = numbers(text)
            values = generated["parameters"]
            self.assertEqual(values["first"] * values["second"], divisor, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], number % divisor, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_two_signs_really_determine_the_remainder(self) -> None:
        """Делители взаимно просты, иначе двух признаков не хватило бы."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            first, second = values["first"], values["second"]
            self.assertEqual(__import__("math").gcd(first, second), 1, f"seed {seed}")
            # По китайской теореме об остатках пара остатков задаёт остаток
            # по произведению однозначно — проверяем это прямым перебором.
            number = values["number"]
            fits = [
                candidate for candidate in range(first * second)
                if candidate % first == number % first
                and candidate % second == number % second
            ]
            self.assertEqual(fits, [values["remainder"]], f"seed {seed}")


class ConsecutiveDigitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["consecutive_numbers_digit_count"]

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def digits_upto(limit: int) -> int:
        """Сколько цифр во всех числах от 1 до limit — прямым подсчётом."""
        return sum(len(str(value)) for value in range(1, limit + 1))

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = int(re.search(rf"выписали (\d+){SPACE}подряд", text).group(1))
            digits = int(re.search(rf"записано (\d+){SPACE}цифр", text).group(1))

            # Решение с нуля: перебираем начало ряда и честно считаем длины
            # чисел строками. Формулу с разрядными границами тест не знает.
            fits = [
                start for start in range(1, 10_000 - count)
                if self.digits_upto(start + count - 1) - self.digits_upto(start - 1) == digits
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: ответ неединственный — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_range_crosses_a_digit_boundary(self) -> None:
        """Иначе число цифр не зависит от начала и ответ не единственный."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(
                len(str(values["first"])), len(str(values["last"])), f"seed {seed}")


class AlternatingSequenceTests(unittest.TestCase):
    TEMPLATE = LIBRARY["alternating_double_and_subtract"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shown = numbers(text)[:8]
            # Правило больше не объявлено в условии — его восстанавливают
            # по самому ряду, как это делает ребёнок: второй член вдвое больше
            # первого, а третий меньше второго на искомую величину.
            gap = shown[1] - shown[2]

            # Решение с нуля: продолжаем ряд по восстановленному правилу
            # и складываем три следующих члена. Заодно проверяется, что все
            # восемь выписанных членов правилу подчиняются.
            sequence = [shown[0]]
            for step in range(10):
                previous = sequence[-1]
                sequence.append(previous * 2 if step % 2 == 0 else previous - gap)
            self.assertEqual(sequence[:8], shown, f"seed {seed}: ряд не по правилу")
            self.assertEqual(generated["answer"], sum(sequence[8:11]), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
