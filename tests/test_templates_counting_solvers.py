"""Приёмы с перебором: проверка решателей независимым перебором.

Здесь особенно важно не повторить логику решателя. Обезьяны кормятся
жадным алгоритмом — он даёт тот же ответ, что и проверка покрытия
пропусками, но приходит к нему иначе. Хорошие числа и звёздочки
пересчитываются сплошным перебором промежутка. Монеты набираются
рекурсией по достоинствам.

Задача про обезьян попала сюда после того, как формула
`min(S/3, S − max)` разошлась с перебором: при запасах 20, 57, 52, 29
она даёт 52, а собрать удаётся только 49.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from itertools import combinations_with_replacement
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(20)
SPACE = "[\\s ]+"


def greedy_triples(counts: list[int]) -> int:
    """Кормим жадно: каждый раз берём три самых многочисленных сорта."""
    stock = sorted(counts, reverse=True)
    fed = 0
    while sum(1 for value in stock if value > 0) >= 3:
        stock.sort(reverse=True)
        for index in range(3):
            stock[index] -= 1
        fed += 1
    return fed


class MonkeysTests(unittest.TestCase):
    TEMPLATE = LIBRARY["monkeys_three_distinct_fruits"]

    def test_matches_greedy_feeding(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            counts = [values["a"], values["b"], values["c"], values["d"]]
            text = generated["rendered_problem"]
            fed = greedy_triples(counts)
            expected = sum(counts) - 3 * fed if "останется" in text else fed
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_simple_formula_would_be_wrong(self) -> None:
        """Жеребьёвка отбирается так, чтобы наивная оценка не сходилась."""
        for seed in SEEDS:
            values = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]
            counts = [values["a"], values["b"], values["c"], values["d"]]
            naive = min(sum(counts) // 3, sum(counts) - max(counts))
            self.assertGreater(naive, greedy_triples(counts),
                               f"seed {seed}: наивная оценка совпала, задача не показательна")


class SmoothNumbersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["products_of_two_primes_count"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            low, high = values["low"], values["low"] + values["span"]
            first, second = values["first"], values["second"]
            text = generated["rendered_problem"]

            # Решение с нуля: делим каждое число промежутка на два множителя,
            # пока делится, и смотрим, осталась ли единица.
            good = []
            for number in range(low, high + 1):
                rest = number
                for divisor in (first, second):
                    while rest % divisor == 0:
                        rest //= divisor
                if rest == 1:
                    good.append(number)
            expected = good[-1] if "самое большое" in text else len(good)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class StarsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["stars_in_number_divisible"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            pattern = re.search(r"числа (\S+) цифрами", text).group(1)
            divisor = int(re.search(r"делилось на (\d+)", text).group(1))

            # Решение с нуля: перебираем все числа нужной длины и оставляем
            # те, что совпадают с образцом по неподвижным цифрам.
            length = len(pattern)
            good = []
            for number in range(10 ** (length - 1), 10 ** length):
                digits = str(number)
                if all(mask == "*" or mask == digit
                       for mask, digit in zip(pattern, digits)) and number % divisor == 0:
                    good.append(number)
            expected = good[-1] if "наибольшее" in text else len(good)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class BalancedNumberTests(unittest.TestCase):
    TEMPLATE = LIBRARY["nth_balanced_digits_number"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            index = int(re.search(r"(\d+)-м\?", text).group(1))

            # Решение с нуля: идём по числам подряд и считаем подходящие.
            seen, value = 0, 9
            while seen < index:
                value += 1
                digits = str(value)
                if sum(1 for digit in digits if int(digit) % 2 == 0) * 2 == len(digits):
                    seen += 1
            self.assertEqual(generated["answer"], value, f"seed {seed}: {text}")


class ExactPaymentTests(unittest.TestCase):
    TEMPLATE = LIBRARY["exact_payment_fixed_coins"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            coins = (values["one"], values["two"], values["three"])
            total, pieces = values["total"], values["pieces"]
            text = generated["rendered_problem"]

            # Решение с нуля: рекурсия по достоинствам, а не сочетания.
            def ways(rest: int, left: int, index: int) -> int:
                if left == 0:
                    return 1 if rest == 0 else 0
                if index == len(coins) or rest < 0:
                    return 0
                return sum(ways(rest - coins[index] * take, left - take, index + 1)
                           for take in range(left + 1))

            found = ways(total, pieces, 0)
            expected = found if "Сколькими способами" in text else found > 0
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class GuaranteedCoinsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["coins_guaranteed_two_kinds"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first = int(re.search(rf"вытащить (\d+){SPACE}монет", text).group(1))
            second = int(re.search(rf"вытащить (\d+){SPACE}монет", text[text.index("Если вытащить"):]).group(1))
            total = int(re.search(rf"оказалось (\d+){SPACE}монет", text).group(1))

            # Решение с нуля: перебираем состав кармана и оставляем те наборы,
            # при которых обе гарантии выполняются.
            fits = [(ones, total - ones) for ones in range(total + 1)
                    if (total - ones) <= first - 1 and ones <= second - 1]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            ones, twos = fits[0]
            expected = twos if "двухрублёвых" in text else ones
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class CurrencyExchangeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["currency_exchange_one_fee"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            fee = int(re.search(r"берут (\d+) юаней", text).group(1))
            amounts = [int(value) for value in
                       re.search(r"было (\d+), (\d+), (\d+) и (\d+) долларов", text).groups()]
            rate = int(re.search(r"дают (\d+) юаней", text).group(1))

            # Решение с нуля: считаем оба способа и сравниваем.
            together = sum(amounts) * rate - fee
            apart = sum(amount * rate - fee for amount in amounts)
            expected = together - apart if "сберегли" in text else together
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
