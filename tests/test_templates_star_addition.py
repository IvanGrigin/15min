"""Независимая проверка сложения со звёздочками.

Решатель шаблона перебирает первое слагаемое и сумму, а второе получает
вычитанием. Тест идёт другим путём: перебирает оба слагаемых и проверяет,
что их сумма подходит под маску. Способ медленнее, зато не повторяет
оптимизацию шаблона — а именно в ней проще всего ошибиться.

Отдельно проверяется корректность задачи. Сами закрытые цифры восстановить
нельзя, расстановок обычно несколько десятков, и это нормально. А вот сумма
закрытых цифр обязана быть одна: иначе верных ответов несколько, а ключ
печатается один.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from itertools import product
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
# Полный перебор обоих слагаемых — это миллион пар на задачу, около секунды.
# Жеребьёвок поэтому немного: смысл теста в независимости пути, а не в объёме.
SEEDS = range(5)


def fill(mask: str) -> list[str]:
    """Все записи, подходящие под маску, без ведущего нуля."""
    stars = [index for index, char in enumerate(mask) if char == "*"]
    if not stars:
        return [mask]
    found = []
    for digits in product("0123456789", repeat=len(stars)):
        chars = list(mask)
        for index, digit in zip(stars, digits):
            chars[index] = digit
        if chars[0] != "0":
            found.append("".join(chars))
    return found


def hidden_sum(mask: str, text: str) -> int:
    return sum(int(digit) for char, digit in zip(mask, text) if char == "*")


class StarAdditionTests(unittest.TestCase):
    TEMPLATE = LIBRARY["star_addition_hidden_sum"]

    def read(self, text: str) -> tuple[str, str, str]:
        first, second, total = re.search(
            r"сложение (\S+) \+ (\S+) = (\S+) звёздочками", text).groups()
        return first, second, total

    def all_hidden_sums(self, first: str, second: str, total: str) -> set[int]:
        """Перебор обоих слагаемых — путь, отличный от шаблонного."""
        sums = set()
        for left in fill(first):
            for right in fill(second):
                whole = str(int(left) + int(right))
                if len(whole) != len(total):
                    continue
                if any(char != "*" and char != digit for char, digit in zip(total, whole)):
                    continue
                sums.add(hidden_sum(first, left) + hidden_sum(second, right)
                         + hidden_sum(total, whole))
        return sums

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            sums = self.all_hidden_sums(*self.read(text))
            self.assertEqual(len(sums), 1, f"seed {seed}: сумма не единственна — {text}")
            self.assertEqual(generated["answer"], sums.pop(), f"seed {seed}: {text}")

    def test_digits_themselves_are_not_recoverable(self) -> None:
        """Если расстановка единственна, это уже другая задача — на восстановление."""
        loose = 0
        for seed in SEEDS:
            first, second, total = self.read(
                generate_active_template(self.TEMPLATE, random.Random(seed))["rendered_problem"])
            fits = [
                (left, right)
                for left in fill(first) for right in fill(second)
                if (whole := str(int(left) + int(right))) and len(whole) == len(total)
                and all(char == "*" or char == digit for char, digit in zip(total, whole))
            ]
            if len(fits) > 1:
                loose += 1
        self.assertEqual(loose, len(SEEDS), "где-то цифры восстанавливаются однозначно")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику: *54** + *82** = 10*793 даёт 43."""
        self.assertEqual(self.all_hidden_sums("*54**", "*82**", "10*793"), {43})

    def test_text_is_clean(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text, f"seed {seed}")
            self.assertNotIn("  ", text, f"seed {seed}")
            self.assertTrue(text[0].isupper(), f"seed {seed}")
            self.assertEqual(text.rstrip()[-1], ".", f"seed {seed}")


if __name__ == "__main__":
    unittest.main()
