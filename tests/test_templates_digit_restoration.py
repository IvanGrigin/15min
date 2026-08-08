"""Батч Б4: восстановление записи числа и счёт вариантов.

Решатели тестов идут в лоб там, где шаблон идёт умно. Вычёркивания
пересчитываются перебором позиций, а не таблицей по разрядам; даты-палиндромы
проверяются посимвольно; восстановление примера ищется полным перебором
всех перестановок и всех замен. На таких размерах перебор ещё посилен,
и именно поэтому он годится в проверку.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(20)


def split_back(digits: str, lengths: tuple[int, int, int]) -> tuple[int, int, int] | None:
    """Разрезать строку на три числа; ведущий ноль делает разбор негодным."""
    first, second, _ = lengths
    parts = (digits[:first], digits[first:first + second], digits[first + second:])
    if any(len(part) > 1 and part[0] == "0" for part in parts):
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


class SwapRestoreTests(unittest.TestCase):
    TEMPLATE = LIBRARY["restore_addition_after_swap"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shown = tuple(int(value) for value in
                          re.search(r"(\d+) \+ (\d+) = (\d+)", text).groups())

            # Решение с нуля: перебираем все пары позиций и проверяем сложение.
            lengths = tuple(len(str(value)) for value in shown)
            digits = "".join(str(value) for value in shown)
            fits = set()
            for left, right in combinations(range(len(digits)), 2):
                if digits[left] == digits[right]:
                    continue
                swapped = list(digits)
                swapped[left], swapped[right] = swapped[right], swapped[left]
                parsed = split_back("".join(swapped), lengths)
                if parsed and parsed[0] + parsed[1] == parsed[2]:
                    fits.add(parsed)
            self.assertEqual(len(fits), 1, f"seed {seed}: восстановлений {len(fits)} — {text}")
            first, _, total = fits.pop()
            expected = total if "сумма в исходном" in text else first
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_shown_example_is_wrong(self) -> None:
        """Показанный пример обязан быть неверным, иначе восстанавливать нечего."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            first, second, total = (int(value) for value in
                                    re.search(r"(\d+) \+ (\d+) = (\d+)", text).groups())
            self.assertNotEqual(first + second, total, f"seed {seed}: {text}")


class ReplacementRestoreTests(unittest.TestCase):
    TEMPLATE = LIBRARY["restore_addition_after_replacement"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            hidden, shown_digit = (int(value) for value in
                                   re.search(r"цифру (\d) заменили на цифру (\d)", text).groups())
            shown = tuple(int(value) for value in
                          re.search(r"(\d+) \+ (\d+) = (\d+)", text).groups())

            # Решение с нуля: перебираем все подмножества показанных цифр.
            lengths = tuple(len(str(value)) for value in shown)
            digits = "".join(str(value) for value in shown)
            places = [index for index, digit in enumerate(digits)
                      if digit == str(shown_digit)]
            fits = set()
            for mask in range(1, 1 << len(places)):
                restored = list(digits)
                for offset, index in enumerate(places):
                    if mask >> offset & 1:
                        restored[index] = str(hidden)
                parsed = split_back("".join(restored), lengths)
                if parsed and parsed[0] + parsed[1] == parsed[2]:
                    fits.add(parsed)
            self.assertEqual(len(fits), 1, f"seed {seed}: восстановлений {len(fits)} — {text}")
            first, second, _ = fits.pop()
            expected = second if "второе слагаемое" in text else first
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class CrossOutDigitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["ways_to_cross_out_digits"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            source, wanted = re.search(r"В (\d+) вычёркивают.+осталось (\d+)", text).groups()

            # Решение с нуля: перебираем, какие позиции оставить.
            expected = sum(
                1 for keep in combinations(range(len(source)), len(wanted))
                if "".join(source[index] for index in keep) == wanted
            )
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class PalindromeDatesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["palindrome_dates_in_years"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first_year, last_year = (int(value) for value in
                                     re.search(r"с (\d{4}) по (\d{4})", text).groups())

            # Решение с нуля: идём по дням и смотрим на запись.
            palindromes = 0
            current = date(first_year, 1, 1)
            while current <= date(last_year, 12, 31):
                written = f"{current.day:02d}{current.month:02d}{current.year:04d}"
                if written == written[::-1]:
                    palindromes += 1
                current += timedelta(days=1)
            years = last_year - first_year + 1
            expected = years - palindromes if "не встретится" in text else palindromes
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class ClassTransfersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["classes_transfers_total_unchanged"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            def pick(pattern: str) -> int:
                return int(re.search(pattern, text).group(1))

            # Каждый переход разбирается своим оборотом: числа классов
            # «8-1», «8-2», «8-3» тоже цифры, и общий разбор их путал.
            one = pick(r"8-1 училось (\d+)")
            two = pick(r"в 8-2 — (\d+), в 8-3")
            three = pick(r"в 8-3 — (\d+)\.")
            first_move = pick(r"физике (\d+)")
            second_move = pick(r"(\d+) — из 8-2 в 8-3")
            third_move = pick(r"а (\d+) — из 8-3 в 8-1")
            fourth = pick(r"из 8-1 в 8-3 ушли (\d+)")
            fifth = pick(r"из 8-3 в 8-2 — (\d+)")
            sixth = pick(r"из 8-2 в 8-1 — (\d+)")
            left = pick(r"литературе (\d+)")

            # Решение с нуля: ведём три счётчика по шагам.
            one -= first_move; two += first_move
            two -= second_move; three += second_move
            three -= third_move; one += third_move
            one -= fourth; three += fourth
            three -= fifth; two += fifth
            two -= sixth; one += sixth
            three -= left
            expected = two if "в классе 8-2" in text else one + two + three
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
