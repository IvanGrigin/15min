"""Независимая проверка второй волны плана на 90%.

Арбуз, мост, перевод квадратных единиц, ряд коробок и наименьшая группа.
Тест каждый раз идёт не тем путём, каким считает шаблон: сухую часть арбуза
он проверяет с обеих сторон, длину моста восстанавливает из долей, ряд
коробок складывает подряд, а наименьшую группу ищет перебором снизу.
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


class WatermelonDryingTests(unittest.TestCase):
    TEMPLATE = LIBRARY["watermelon_drying_percent"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            fresh = int(re.search(r"весил (\d+)", text).group(1))
            wet, dry = (int(v) for v in re.findall(r"(\d+)%", text))
            answer = generated["answer"]

            # Решение с нуля: сухая часть не испаряется, значит её вес
            # одинаков до и после. Считаем его с обеих сторон.
            solid_before = Fraction(fresh) * Fraction(100 - wet, 100)
            solid_after = Fraction(answer) * Fraction(100 - dry, 100)
            self.assertEqual(solid_before, solid_after, f"seed {seed}: {text}")
            self.assertLess(answer, fresh, f"seed {seed}: подсохший стал тяжелее")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 10 кг при 99% воды после подсыхания до 98% — это 5 кг."""
        self.assertEqual(Fraction(10) * Fraction(1, 100), Fraction(5) * Fraction(2, 100))


class BridgeLengthTests(unittest.TestCase):
    TEMPLATE = LIBRARY["bridge_over_river_length"]

    PARTS = {"четверть": 4, "пятая часть": 5, "шестая часть": 6,
             "восьмая часть": 8, "десятая часть": 10}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            river = int(re.search(r"шириной (\d+)", text).group(1))
            denominator = next(d for word, d in self.PARTS.items() if word in text)
            answer = generated["answer"]

            # Решение с нуля: над водой висит то, что осталось после берегов.
            over_water = Fraction(answer) * (1 - Fraction(2, denominator))
            self.assertEqual(over_water, river, f"seed {seed}: {text}")
            self.assertGreater(answer, river, f"seed {seed}: мост короче реки")

    def test_source_example_reproduces(self) -> None:
        """Контроль: по пятой части на берег и река 120 метров — мост 200."""
        self.assertEqual(200 * (1 - Fraction(2, 5)), 120)


class SquareUnitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_units_conversion"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            ratio = int(re.search(r"— (\d+) ", text).group(1))
            count = int(re.search(r"в (\d+) квадратных", text).group(1))

            # Решение с нуля: выкладываем квадрат стороной ratio маленькими
            # квадратиками — их ровно ratio строк по ratio штук.
            in_one = sum(ratio for _ in range(ratio))
            self.assertEqual(generated["answer"], count * in_one, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: в трёх квадратных футах 432 квадратных дюйма."""
        self.assertEqual(3 * 12 * 12, 432)


class BoxesRowTests(unittest.TestCase):
    TEMPLATE = LIBRARY["boxes_growing_row_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            extra = int(re.search(r"на (\d+) больше", text).group(1))
            full = int(re.search(r"было бы всего (\d+)", text).group(1))

            # Решение с нуля: складываем подряд, пока не наберём обещанную
            # сумму. Так находится, сколько коробок было бы.
            running = 0
            grown = 0
            while running < full:
                grown += 1
                running += grown
            self.assertEqual(running, full, f"seed {seed}: сумма недостижима — {text}")

            boxes = grown - extra
            self.assertEqual(generated["answer"], boxes * (boxes + 1) // 2,
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 5050 — сумма до ста; при 97 коробках выходит 4753."""
        self.assertEqual(100 * 101 // 2, 5050)
        self.assertEqual(97 * 98 // 2, 4753)


class MinimalGroupTests(unittest.TestCase):
    TEMPLATE = LIBRARY["minimal_group_by_percent"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            percent = int(re.search(r"больше (\d+)%", text).group(1))

            # Решение с нуля: перебираем размер группы снизу и ищем первый,
            # при котором большинство может превысить порог, а меньшинство
            # остаётся непустым.
            fits = next(
                total for total in range(2, 500)
                if any(Fraction(major, total) * 100 > percent
                       for major in range(1, total))
            )
            self.assertEqual(generated["answer"], fits, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: при 94% наименьшая группа — 17 человек."""
        self.assertGreater(Fraction(16, 17) * 100, 94)
        self.assertLessEqual(Fraction(15, 16) * 100, 94)



class ApplesSharesTests(unittest.TestCase):
    """Две доли берутся от разного: первая от целого, вторая от остатка."""

    TEMPLATE = LIBRARY["apples_boxes_and_shares"]

    PARTS = {"Шестую": 6, "Четвёртую": 4, "Пятую": 5, "Третью": 3,
             "шестую": 6, "четвёртую": 4, "пятую": 5, "третью": 3, "половину": 2}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first = int(re.search(r"было (\d+) кг", text).group(1))
            times = int(re.search(r"в (\d+) раза больше", text).group(1))
            per_box = int(re.search(r"по (\d+) кг", text).group(1))
            shop = self.PARTS[re.search(r"(\S+) часть всех ящиков", text).group(1)]
            juice = self.PARTS[re.search(r"а (\S+) часть остатка", text).group(1)]

            # Решение с нуля: считаем ящики и вывозим их по очереди.
            boxes = (first + first * times) // per_box
            self.assertEqual((first + first * times) % per_box, 0,
                             f"seed {seed}: ящики не целые — {text}")
            after_shop = boxes - boxes // shop
            after_juice = after_shop - after_shop // juice
            self.assertEqual(generated["answer"], after_juice, f"seed {seed}: {text}")

    def test_shares_are_not_additive(self) -> None:
        """Контроль смысла: сложить доли и вычесть — другой, неверный ответ."""
        boxes = 96
        correct = (boxes - boxes // 4) - (boxes - boxes // 4) // 4
        naive = boxes - boxes // 4 - boxes // 4
        self.assertEqual(correct, 54)
        self.assertNotEqual(correct, naive)


class TravelerBackwardsTests(unittest.TestCase):
    """С конца задача решается в уме, вперёд — только уравнением."""

    TEMPLATE = LIBRARY["traveler_four_days_backwards"]

    PARTS = {"пятую часть": 5, "четвёртую часть": 4, "третью часть": 3, "половину": 2}

    def read_share(self, phrase: str) -> int:
        for word, denominator in self.PARTS.items():
            if phrase.startswith(word):
                return denominator
        raise AssertionError(f"незнакомая доля: {phrase}")

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shares = [
                self.read_share(re.search(pattern, text).group(1))
                for pattern in (r"\S+ (\S+ ?\S*) всего пути", r"— (\S+ ?\S*) остатка",
                                r"— (\S+ ?\S*) оставшегося")
            ]
            extras = [int(v) for v in re.findall(r"и ещё (\d+) км", text)]
            tail = int(re.search(r"Последние (\d+) км", text).group(1))
            total = generated["answer"]

            # Решение с нуля: идём вперёд от найденного пути и проверяем,
            # что на четвёртый день остаётся ровно обещанное.
            left = Fraction(total)
            for share, extra in zip(shares, extras):
                left = left - (left / share + extra)
            self.assertEqual(left, tail, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: доли 1/5, 1/2, 1/4 с добавками 2, 1, 3 и хвостом 18 — 75 км."""
        left = Fraction(75)
        for share, extra in ((5, 2), (2, 1), (4, 3)):
            left = left - (left / share + extra)
        self.assertEqual(left, 18)


class TrucksLoadTests(unittest.TestCase):
    """Последняя машина уедет недогруженной, но она всё равно нужна."""

    TEMPLATE = LIBRARY["trucks_for_warehouse_load"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            boxes, box_kg = (int(v) for v in re.search(
                r"лежат (\d+) \S+ массой по (\d+) кг", text).groups())
            crates, crate_kg = (int(v) for v in re.search(
                r"и (\d+) \S+ по (\d+) кг", text).groups())
            tons = int(re.search(r"грузоподъёмностью (\d+)", text).group(1))

            # Решение с нуля: грузим машины подряд, пока груз не кончится.
            left = boxes * box_kg + crates * crate_kg
            capacity = tons * 1000
            trucks = 0
            while left > 0:
                left -= capacity
                trucks += 1
            self.assertEqual(generated["answer"], trucks, f"seed {seed}: {text}")

    def test_rounding_really_matters(self) -> None:
        """Жеребьёвка обязана давать остаток: иначе округление незаметно."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            boxes, box_kg = (int(v) for v in re.search(
                r"лежат (\d+) \S+ массой по (\d+) кг", text).groups())
            crates, crate_kg = (int(v) for v in re.search(
                r"и (\d+) \S+ по (\d+) кг", text).groups())
            tons = int(re.search(r"грузоподъёмностью (\d+)", text).group(1))
            self.assertNotEqual((boxes * box_kg + crates * crate_kg) % (tons * 1000), 0,
                                f"seed {seed}: груз делится нацело — {text}")


if __name__ == "__main__":
    unittest.main()
