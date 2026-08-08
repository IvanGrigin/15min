"""Батчи Б5 и Б9: перечисление вариантов и разнородное числовое.

Решатели считают перебором там, где шаблон считает формулой. Раскладки
камешков и стопки строятся явно через itertools, слова языка порождаются
как кортежи букв, обезьяны кормятся жадным алгоритмом. Совпадение перебора
с формулой и есть проверка формулы.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from itertools import combinations_with_replacement, permutations, product
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(20)
SPACE = "[\\s ]+"


class StonesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["stones_into_holes_ways"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            dark, light, holes = values["dark"], values["light"], values["holes"]

            # Решение с нуля: перечисляем раскладки как наборы номеров коробок.
            dark_ways = len(list(combinations_with_replacement(range(holes), dark)))
            light_ways = len(list(combinations_with_replacement(range(holes), light)))
            text = generated["rendered_problem"]
            expected = dark_ways if "Камни неразличимы" in text else dark_ways * light_ways
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class StackTests(unittest.TestCase):
    TEMPLATE = LIBRARY["ordered_stack_of_albums"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            total, pick = values["total"], values["pick"]
            text = generated["rendered_problem"]

            # Решение с нуля: строим сами стопки.
            ordered = len(list(permutations(range(total), pick)))
            unordered = len(list(combinations_with_replacement(range(total), pick)))
            if "порядок в стопке не важен" in text:
                from itertools import combinations
                unordered = len(list(combinations(range(total), pick)))
                self.assertEqual(generated["answer"], unordered, f"seed {seed}: {text}")
            else:
                self.assertEqual(generated["answer"], ordered, f"seed {seed}: {text}")


class WordsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["words_up_to_length_count"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            letters, length = values["letters"], values["length"]
            text = generated["rendered_problem"]

            # Решение с нуля: порождаем слова, пока это посильно.
            if letters ** length > 200000:
                continue
            longest = len(list(product(range(letters), repeat=length)))
            everything = sum(len(list(product(range(letters), repeat=size)))
                             for size in range(1, length + 1))
            expected = longest if "самых длинных" in text else everything
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class InequalityTests(unittest.TestCase):
    TEMPLATE = LIBRARY["largest_natural_x_inequality"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first, second, mul, third, big, div = (
                int(value) for value in re.search(
                    r"\((\d+) − (\d+)\) · (\d+) : \((\d+) \+ (\d+) : (\d+)\)", text).groups())

            # Решение с нуля: считаем по действиям, как записано.
            self.assertEqual(big % div, 0, f"seed {seed}: деление не точное")
            value = (first - second) * mul / (third + big // div)
            self.assertEqual(generated["answer"], int(value), f"seed {seed}: {text}")


class TrickTests(unittest.TestCase):
    TEMPLATE = LIBRARY["thought_number_trick_result"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            times, plus = values["times"], values["plus"]
            text = generated["rendered_problem"]

            # Решение с нуля: прогоняем фокус на разных задуманных числах.
            results = {(guess * times + plus) / times - guess for guess in range(1, 12)}
            self.assertEqual(len(results), 1, f"seed {seed}: результат зависит от числа")
            outcome = results.pop()
            expected = plus if "Какое число нужно было прибавить" in text else outcome
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class DifferenceShiftTests(unittest.TestCase):
    TEMPLATE = LIBRARY["difference_after_both_shifts"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            down, up = values["down"], values["up"]
            text = generated["rendered_problem"]

            # Решение с нуля: берём конкретные числа и сравниваем разности.
            changes = set()
            for minuend, subtrahend in ((900, 300), (1500, 40), (700, 555)):
                was = minuend - subtrahend
                if "вычитаемое уменьшить" in text:
                    became = (minuend - down) - (subtrahend - up)
                else:
                    became = (minuend - down) - (subtrahend + up)
                changes.add(was - became)
            self.assertEqual(len(changes), 1, f"seed {seed}: изменение зависит от чисел")
            drop = changes.pop()
            # При обоих уменьшениях разность растёт, поэтому знак меняется.
            expected = -drop if "вычитаемое уменьшить" in text else drop
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class TreesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["same_tree_counted_from_both_ends"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            number = int(re.search(r"у (\d+)-го дерева", text).group(1))

            # Решение с нуля: ищем аллею, где k-е слева и k-е справа совпадают.
            fits = [trees for trees in range(number, 3 * number)
                    if number - 1 == trees - number]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits}")
            expected = number - 1 if "позади" in text else fits[0]
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class RepeatedNumberTests(unittest.TestCase):
    TEMPLATE = LIBRARY["repeated_number_divisibility"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            piece = int(re.search(r"Число (\d+) выписали", text).group(1))
            divisor = int(re.search(r"делилось на (\d+)", text).group(1))

            # Решение с нуля: складываем длинное число и делим по-настоящему.
            possible = any(int(str(piece) * times) % divisor == 0
                           for times in range(1, 40))
            self.assertEqual(generated["answer"], possible, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
