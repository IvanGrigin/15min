"""Батч Б2: доли пути и времени.

Решатели считают не по формулам шаблонов, а по определению: путь берётся
за единицу, движение раскладывается на участки, и время каждого получается
делением. Там, где шаблон выводит ответ короткой дробью, тест приходит
к нему длинной дорогой — это и есть проверка, что дробь выведена верно.
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
SEEDS = range(30)
SPACE = "[\\s ]+"


class AverageSpeedTests(unittest.TestCase):
    TEMPLATE = LIBRARY["average_speed_half_path_half_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            slow, fast = (int(value) for value in
                          re.findall(r"скоростью (\d+) км/ч", text)[:2])

            # Решение с нуля: берём путь 1 и время 1, считаем прямо по смыслу.
            time_by_path = Fraction(1, 2) / slow + Fraction(1, 2) / fast
            speed_by_path = 1 / time_by_path
            path_by_time = Fraction(slow, 2) + Fraction(fast, 2)
            speed_by_time = path_by_time / 1

            # Язык выражений делит через float, поэтому ответ приходит числом
            # с плавающей точкой. Сравниваем не приблизительно: печатное
            # представление переводится обратно в точную дробь, и она обязана
            # совпасть с посчитанной здесь.
            def exact(value: object) -> Fraction:
                return Fraction(str(value))

            answer = generated["answer"]
            if isinstance(answer, list):
                self.assertEqual([exact(item) for item in answer],
                                 [speed_by_path, speed_by_time], f"seed {seed}: {text}")
            else:
                self.assertEqual(exact(answer), speed_by_time, f"seed {seed}: {text}")
            self.assertLess(speed_by_path, speed_by_time,
                            f"seed {seed}: по пути должно быть медленнее")


class DelayFirstHalfTests(unittest.TestCase):
    TEMPLATE = LIBRARY["delay_on_first_half_speedup"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            usual = int(re.search(rf"домой (\d+){SPACE}минут", text).group(1))
            extra = int(re.search(rf"лишние (\d+){SPACE}минут", text).group(1))

            # Решение с нуля: половина пути занимает половину привычного времени.
            half = Fraction(usual, 2)
            left = half - extra
            self.assertGreater(left, 0, f"seed {seed}: времени не осталось — {text}")
            if "Сколько минут остаётся" in text:
                self.assertEqual(generated["answer"], left, f"seed {seed}: {text}")
            else:
                self.assertEqual(generated["answer"], half / left, f"seed {seed}: {text}")


class OvershootHomeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["overshoot_home_return_faster"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))
            hours = int(re.search(rf"через (\d+){SPACE}час", text).group(1))

            # Решение с нуля: берём любые расстояния и скорость и складываем
            # четыре участка. Ответ не должен от них зависеть — это и проверяем.
            for shop, over, speed in ((7, 3, 2), (12, 5, 3), (9, 1, 4)):
                away = Fraction(shop, speed) + Fraction(over, times * speed)
                toward = Fraction(shop, times * speed) + Fraction(over, times * times * speed)
                share_away = away / (away + toward)
                minutes = hours * 60
                expected = share_away * minutes
                if "приближаясь" in text:
                    expected = minutes - expected
                self.assertEqual(generated["answer"], expected,
                                 f"seed {seed} при пробе {shop}/{over}/{speed}: {text}")


class ThreeLegsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_legs_halved_one_by_one"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(rf"этапа за (\d+){SPACE}минут", text).group(1))
            save_sit = int(re.search(rf"на (\d+){SPACE}минут раньше", text).group(1))
            save_run = int(re.search(rf"выиграл[а]? (\d+){SPACE}минут", text).group(1))

            # Решение с нуля: подбираем длительности трёх этапов так, чтобы
            # оба описанных года сошлись, и лишь потом считаем третий.
            fits = [
                (sit, run) for sit in range(2, total, 2) for run in range(2, total, 2)
                if sit - sit // 2 == save_sit and run - run // 2 == save_run
                and total - sit - run > 0
            ]
            self.assertTrue(fits, f"seed {seed}: этапы не подбираются — {text}")
            sit, run = fits[0]
            ride = total - sit - run
            expected = ride if "велосипедный этап" in text else total - ride // 2
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class HareRestTests(unittest.TestCase):
    TEMPLATE = LIBRARY["hare_rest_tortoise_left"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            distance = int(re.search(rf"длиной (\d+){SPACE}метр", text).group(1))
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))

            # Решение с нуля: скорость медленного берём за единицу, дальше
            # просто складываем три отрезка времени быстрого.
            slow_speed = Fraction(1)
            fast_speed = times * slow_speed
            leg = Fraction(distance, 2) / fast_speed
            fast_total = leg + leg + leg          # бег, привал такой же, снова бег
            passed = slow_speed * fast_total
            expected = passed if "пробежал" in text else distance - passed
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_fast_one_wins(self) -> None:
        """Быстрый обязан успеть первым, иначе вопрос теряет смысл."""
        for seed in SEEDS:
            values = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertGreater(2 * values["times"], 3, f"seed {seed}")


if __name__ == "__main__":
    unittest.main()
