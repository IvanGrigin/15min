"""Независимая проверка: калькулятор, поезда, автобус, улитка, обезьяны, полки.

Каждый решатель теста идёт своим путём. Калькулятор — прямым моделированием
ошибки. Поезда — по секундам сближения. Улитка — по часам, шаг за шагом.
Обезьяны — сложением скоростей в дробях. Полки — перебором худшего случая.
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


class CalculatorExtraZeroTests(unittest.TestCase):
    TEMPLATE = LIBRARY["calculator_extra_zero"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            wanted = int(re.search(r"вместо (\d+)", text).group(1))
            got = int(re.search(r"получилось (\d+)", text).group(1))
            second = generated["answer"]

            # Решение с нуля: восстанавливаем первое слагаемое и повторяем
            # обе операции — верную и ошибочную.
            first = wanted - second
            self.assertEqual(first + second, wanted, f"seed {seed}: {text}")
            self.assertEqual(first + int(f"{second}0"), got, f"seed {seed}: {text}")
            self.assertGreater(first, 0, f"seed {seed}: первое слагаемое не положительно")

    def test_source_example_reproduces(self) -> None:
        """Контроль: вместо 1222 вышло 5551, значит второе число 481."""
        self.assertEqual((5551 - 1222) // 9, 481)
        self.assertEqual((1222 - 481) + 4810, 5551)


class TwoTrainsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_trains_pass_each_other"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length = int(re.search(r"длиной (\d+) м", text).group(1))
            speed = int(re.search(r"скоростью (\d+) км/ч", text).group(1))

            # Решение с нуля: считаем по секундам, пока хвосты не поравняются.
            per_second = Fraction(speed * 1000, 3600)
            closing = 2 * per_second
            need = 2 * length
            seconds = Fraction(need, 1) / closing
            self.assertEqual(seconds.denominator, 1, f"seed {seed}: не целые секунды")
            self.assertEqual(generated["answer"], int(seconds), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 50 метров при 45 км/ч — 4 секунды."""
        self.assertEqual(Fraction(100) / (2 * Fraction(45000, 3600)), 4)


class WalkOrBusTests(unittest.TestCase):
    TEMPLATE = LIBRARY["walk_or_bus_round_trip"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            mixed = int(re.search(r"уходит (\d+)", text).group(1))
            by_bus = int(re.search(r"занимает (\d+)", text).group(1))

            # Решение с нуля: находим обе односторонние дороги по отдельности
            # и проверяем оба данных условия.
            bus_one_way = Fraction(by_bus, 2)
            walk_one_way = mixed - bus_one_way
            self.assertEqual(walk_one_way + bus_one_way, mixed, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], 2 * walk_one_way, f"seed {seed}: {text}")
            self.assertGreater(walk_one_way, bus_one_way, f"seed {seed}: пешком быстрее автобуса")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 90 минут смешанно и 30 на автобусе — 150 минут пешком."""
        self.assertEqual(2 * (90 - 30 // 2), 150)


class SnailClimbTests(unittest.TestCase):
    TEMPLATE = LIBRARY["snail_climbs_tree"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            height = int(re.search(r"высотой (\d+) м", text).group(1))
            up = int(re.search(r"поднимается на (\d+) м", text).group(1))
            down = int(re.search(r"сползает на (\d+) м", text).group(1))

            # Решение с нуля: считаем по часам. Достигнув вершины, улитка
            # больше не сползает — цикл прерывается сразу.
            position = 0
            hours = 0
            while True:
                position += up
                hours += 1
                if position >= height:
                    break
                position -= down
                hours += 1
            self.assertEqual(position, height, f"seed {seed}: вершина взята не ровно")
            self.assertEqual(generated["answer"], hours, f"seed {seed}: {text}")

    def test_last_climb_has_no_slide(self) -> None:
        """Контроль смысла: наивное деление высоты даёт другой, больший ответ."""
        height, up, down = 17, 3, 1
        naive = 2 * (height // (up - down))
        position, hours = 0, 0
        while position < height:
            position += up
            hours += 1
            if position >= height:
                break
            position -= down
            hours += 1
        self.assertLess(hours, naive)


class MonkeysTests(unittest.TestCase):
    TEMPLATE = LIBRARY["cheerful_and_sad_monkeys"]

    WORDS = {"Одна": 1, "Две": 2, "Три": 3, "одна": 1, "две": 2, "три": 3,
             "четыре": 4, "пять": 5, "шесть": 6}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first_happy, first_sad = self.read(text.split("съедают")[0])
            second_part = text.split(", а ")[1]
            second_happy, second_sad = self.read(second_part.split(" — ")[0])
            times = [int(v) for v in re.findall(r"за (\d+)", text)]
            answer = generated["answer"]

            # Решение с нуля: скорости складываются, а времена — нет.
            # Проверяем оба наблюдения через найденную скорость весёлой.
            happy = Fraction(1, answer)
            first_total = Fraction(1, times[0])
            sad = (first_total - first_happy * happy) / first_sad
            self.assertGreater(sad, 0, f"seed {seed}: грустная обезьяна не ест")
            self.assertEqual(second_happy * happy + second_sad * sad,
                             Fraction(1, times[1]), f"seed {seed}: {text}")

    def read(self, part: str) -> tuple[int, int]:
        words = re.findall(r"(\S+) (?:весёл|грустн)\S+", part)
        self.assertEqual(len(words), 2, f"не разобрано: {part}")
        return self.WORDS[words[0]], self.WORDS[words[1]]

    def test_source_example_reproduces(self) -> None:
        """Контроль: 1 + 2 за час и 4 + 2 за 20 минут — весёлая за 90 минут."""
        happy = (Fraction(1, 20) - Fraction(1, 60)) / 3
        self.assertEqual(happy, Fraction(1, 90))


class ShelvesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["shelves_guaranteed_find"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            shelves = int(re.search(r"Среди (\d+) книжных полок", text).group(1))
            with_a = int(re.search(r"полок (\d+) содержат", text).group(1))
            with_b = int(re.search(r"содержат \S+ ?\S*, (\d+) —", text).group(1))

            # Решение с нуля: перебираем, сколько полок осматриваем, и ищем
            # первое число, при котором худший случай уже не спасает.
            answer = next(
                looked for looked in range(1, shelves + 1)
                if looked > shelves - with_a and looked > shelves - with_b
            )
            self.assertEqual(generated["answer"], answer, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: из 7 полок романы на 5, стихи на 4 — осмотреть 4."""
        self.assertEqual(max(7 - 5, 7 - 4) + 1, 4)


if __name__ == "__main__":
    unittest.main()
