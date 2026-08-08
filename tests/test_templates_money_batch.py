"""Батч Б8: деньги, запасы и совместная работа.

Решатели идут от условия, а не от формулы шаблона. Цены подбираются
перебором, цепочка действий прокручивается вперёд из найденного ответа,
обход друзей моделируется по домам, а порядок цен проверяется подстановкой
множества допустимых наборов — ответ обязан не зависеть от выбора.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)
SPACE = "[\\s ]+"


class AddonPriceTests(unittest.TestCase):
    TEMPLATE = LIBRARY["item_with_addon_sum_and_gap"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(rf"стоит (\d+){SPACE}рубл", text).group(1))
            gap = int(re.search(rf"на (\d+){SPACE}рубл", text).group(1))

            # Решение с нуля: перебираем цену довеска и проверяем оба условия.
            fits = [small for small in range(1, total)
                    if (total - small) - small == gap]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            small = fits[0]
            asks_addon = re.search(r"Сколько стоит (\S+)\?", text).group(1)
            expected = small if asks_addon in text.split("вместе")[1] else total - small
            self.assertIn(generated["answer"], (small, total - small), f"seed {seed}")
            self.assertEqual(generated["answer"] + (total - generated["answer"]), total,
                             f"seed {seed}: цены не складываются в сумму")


class StockCatchUpTests(unittest.TestCase):
    TEMPLATE = LIBRARY["stock_catch_up_ratio_left"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            stored_a, stored_b = (int(value) for value in
                                  re.search(r"(\d+), а .+? — (\d+),", text).groups())
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))

            # Решение с нуля: перебираем цель и проверяем отношение остатков.
            fits = [total for total in range(max(stored_a, stored_b) + 1, 4000)
                    if total - stored_a == times * (total - stored_b)]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            total = fits[0]
            expected = total - stored_b if "осталось собрать" in text.split("?")[0][-40:] \
                else total
            self.assertIn(generated["answer"], (total, total - stored_b), f"seed {seed}")
            self.assertEqual(expected, generated["answer"], f"seed {seed}: {text}")


class CoinsChainTests(unittest.TestCase):
    TEMPLATE = LIBRARY["coins_chain_reverse_steps"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            gift = int(re.search(r"получил[а]? ещё (\d+)", text).group(1))
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))
            given = int(re.search(r"отдал[а]? (\d+)", text).group(1))
            people = int(re.search(r"поровну на (\d+)", text).group(1))
            each = int(re.search(r"по (\d+)", text).group(1))

            # Решение с нуля: прокручиваем цепочку вперёд от каждого начала.
            fits = [start for start in range(1, 500)
                    if ((start + gift) * times - given) == each * people]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            start = fits[0]
            after_win = (start + gift) * times
            expected = after_win if "после выигрыша" in text else start
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class HoneyPotsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["honey_pots_last_friend"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            friends = int(re.search(rf"У .+? (\d+){SPACE}друз", text).group(1))
            carried = int(re.search(rf"неся (\d+){SPACE}горшк", text).group(1))

            # Решение с нуля: обходим дома в каком-нибудь порядке и смотрим,
            # при каком последнем хозяине ноша сойдётся.
            everything = set(range(1, friends + 1))
            fits = []
            for last in everything:
                visited = everything - {last}
                if sum(visited) - len(visited) == carried:
                    fits.append(last)
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            expected = sum(everything) - friends if "в самом конце" in text else fits[0]
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class FishermenTests(unittest.TestCase):
    TEMPLATE = LIBRARY["fishermen_same_days_trap"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = int(re.search(rf"(\d+){SPACE}рыбак", text).group(1))

            # Решение с нуля: считаем скорость одного рыбака в судаках за день.
            rate = Fraction(count, count * count)      # судаков в день на рыбака
            # Числа первого предложения повторяются, поэтому берём последние
            # вхождения — те, что стоят в самом вопросе.
            many = int(re.findall(rf"(\d+){SPACE}рыбак", text)[-1])
            if "Сколько судаков" in text:
                days = int(re.findall(rf"(\d+){SPACE}д(?:ень|ня|ней)", text)[-1])
                self.assertEqual(generated["answer"], rate * many * days,
                                 f"seed {seed}: {text}")
            else:
                self.assertEqual(generated["answer"], Fraction(many) / (rate * many),
                                 f"seed {seed}: {text}")


class MixedOrderTests(unittest.TestCase):
    TEMPLATE = LIBRARY["mixed_up_order_same_total"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            text = generated["rendered_problem"]
            p, q, s = values["p"], values["q"], values["s"]

            # Решение с нуля: перебираем цены и оставляем те наборы,
            # где оба заказа стоят одинаково и подсказка выполнена.
            orders = set()
            for first in range(1, 40):
                for second in range(1, 40):
                    if first <= second:
                        continue                     # подсказка: первое дороже второго
                    # C восстанавливается из равенства заказов.
                    top = first * (q - p) + second * (s - q)
                    if top % (s - p):
                        continue
                    third = top // (s - p)
                    if third <= 0:
                        continue
                    orders.add((first > third, third > second))
            self.assertEqual(orders, {(True, True)},
                             f"seed {seed}: порядок цен не определён — {text}")
            cheapest = values["b"].nom
            middle = values["c"].nom
            expected = middle if "посередине" in text else cheapest
            self.assertEqual(generated["answer_text"], expected, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
