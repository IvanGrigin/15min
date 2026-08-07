"""Независимая проверка шаблонов темы «Часы, циферблаты и электронные табло».

Каждый решатель решает задачу с нуля и другим способом, чем шаблон: где шаблон
пользуется закрытой формулой, тест перебирает. Совпадение перебора с формулой
и есть проверка — повторение формулы шаблона проверкой не было бы.
"""
from __future__ import annotations

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
DRIFTING = LIBRARY["drifting_watches_same_time"]
ROUTINE = LIBRARY["routine_sign_true_hours"]
TOWERS = LIBRARY["tower_clocks_meet"]
CUCKOO = LIBRARY["cuckoo_full_turns"]
SEEDS = range(25)


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    """Общие требования к любому сгенерированному условию."""
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class DriftingWatchesTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(DRIFTING, random.Random(seed))
            text = generated["rendered_problem"]

            # Числа берём из отрендеренного условия, а не из parameters:
            # так решатель пользуется ровно тем, что видит ученик, и не может
            # опереться на промежуточные величины шаблона.
            drifts = [int(value) for value in re.findall(r"на (\d+)\xa0минут", text)]
            readings = [int(value) for value in re.findall(r"(\d+):00", text)]
            self.assertEqual(len(drifts), 2, f"seed {seed}: {text}")
            self.assertEqual(len(readings), 2, f"seed {seed}: {text}")
            fast, slow = drifts
            hour_a, hour_b = readings

            # Решение с нуля: минута за минутой прокручиваем сутки и смотрим,
            # когда показания сойдутся. Никакой модульной арифметики шаблона.
            drift = fast + slow
            difference = (hour_a - hour_b) * 60 % 1440
            days = 0
            while True:
                days += 1
                difference = (difference + drift) % 1440
                if difference == 0:
                    break
                self.assertLess(days, 5000, f"seed {seed}: сходимости нет")

            self.assertEqual(generated["answer"], days, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_owner_named_for_each_watch(self) -> None:
        """Аудит нашёл в источнике «первые/вторые» часы — здесь у каждых есть владелец."""
        for seed in SEEDS:
            generated = generate_active_template(DRIFTING, random.Random(seed))
            text = generated["rendered_problem"]
            self.assertNotIn("первые часы", text.lower(), f"seed {seed}")
            self.assertNotIn("вторые часы", text.lower(), f"seed {seed}")
            # У каждых часов назван владелец: имя в родительном падеже стоит
            # и там, где описан ход, и там, где даны показания.
            for role in ("a", "b"):
                owner = generated["parameters"][role].get_case("gen")
                self.assertGreaterEqual(
                    text.count(owner), 2,
                    f"seed {seed}: {owner} упомянут {text.count(owner)} раз(а)",
                )

    def test_readings_are_two_digit_hours(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(DRIFTING, random.Random(seed))["parameters"]
            self.assertGreaterEqual(values["hour_a"], 10, f"seed {seed}")
            self.assertGreaterEqual(values["hour_b"], 10, f"seed {seed}")


class RoutineSignTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(ROUTINE, random.Random(seed))
            text = generated["rendered_problem"]
            hours = [int(value) for value in re.findall(r"(\d+)\xa0час", text)]
            self.assertEqual(len(hours), 2, f"seed {seed}: {text}")
            forward, backward = hours

            # Решение с нуля: честно перебираем 24 часа суток и сравниваем
            # занятие в двух моментах. Шаблон считает это закрытой формулой.
            def sleeping(hour: int) -> bool:
                return (hour % 24) >= 12

            expected = sum(
                sleeping(hour + forward) == sleeping(hour - backward)
                for hour in range(24)
            )

            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_source_examples_reproduce(self) -> None:
        """Контроль по исходным задачам 310 и 328."""
        def sleeping(hour: int) -> bool:
            return (hour % 24) >= 12

        def count(forward: int, backward: int) -> int:
            return sum(sleeping(h + forward) == sleeping(h - backward) for h in range(24))

        self.assertEqual(count(1, 2), 18)
        self.assertEqual(count(2, 3), 14)

    def test_past_tense_agrees_with_gender(self) -> None:
        seen_feminine = False
        for seed in range(120):
            generated = generate_active_template(ROUTINE, random.Random(seed))
            hero = generated["parameters"]["hero"]
            text = generated["rendered_problem"]
            if hero.gender == "f":
                seen_feminine = True
                self.assertIn("повесила", text, f"seed {seed}: {hero.nom}")
                self.assertIn("делала", text, f"seed {seed}: {hero.nom}")
            elif hero.gender == "m":
                self.assertIn("повесил ", text, f"seed {seed}: {hero.nom}")
                self.assertIn("делал ", text, f"seed {seed}: {hero.nom}")
        self.assertTrue(seen_feminine, "за 120 сидов не встретилось женского персонажа")


class TowerClocksTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(TOWERS, random.Random(seed))
            text = generated["rendered_problem"]

            # Даты и часы вытаскиваем из условия: «14 марта, 14 часов».
            pairs = re.findall(r"(\d+)\s+\S+,\s+(\d+)\xa0час", text)
            self.assertEqual(len(pairs), 2, f"seed {seed}: {text}")
            (day1, hour1), (day2, hour2) = [(int(a), int(b)) for a, b in pairs]

            # Решение с нуля: двигаем часы по одному часу навстречу друг другу,
            # пока показания не совпадут. Деление пополам не используется.
            forward = day1 * 24 + hour1
            backward = day2 * 24 + hour2
            elapsed = 0
            while forward != backward:
                forward += 1
                backward -= 1
                elapsed += 1
                self.assertLess(elapsed, 1000, f"seed {seed}: часы разминулись")

            self.assertEqual(generated["answer"], elapsed, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_source_examples_reproduce(self) -> None:
        """Контроль по исходным задачам 274 и 292."""
        def meet(days_gap: int, hour1: int, hour2: int) -> int:
            forward, backward, elapsed = hour1, days_gap * 24 + hour2, 0
            while forward != backward:
                forward, backward, elapsed = forward + 1, backward - 1, elapsed + 1
            return elapsed

        self.assertEqual(meet(5, 18, 10), 56)
        self.assertEqual(meet(4, 14, 8), 45)

    def test_both_dates_stay_inside_one_month(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(TOWERS, random.Random(seed))["parameters"]
            self.assertLessEqual(values["day2"], 28, f"seed {seed}")
            self.assertGreater(values["day2"], values["day1"], f"seed {seed}")


class CuckooTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(CUCKOO, random.Random(seed))
            text = generated["rendered_problem"]
            turns = generated["parameters"]["turns"]
            # Циферблат и половины читаются из условия, как их читает ученик:
            # часы в этой теме бывают странные, на 10 или 24 часа.
            dial = int(re.search(r"разделён на (\d+)[\s\xa0]час", text).group(1))
            half = "на каждой половине часа" in text

            # Решение с нуля: считаем бои час за часом, начиная с произвольного
            # часа, — сумма не зависит от начала, и это тоже проверяется.
            for start in (1, 5, dial):
                strikes = 0
                for step in range(dial * turns):
                    strikes += (start + step - 1) % dial + 1
                    if half:
                        strikes += 1
                self.assertEqual(generated["answer"], strikes, f"seed {seed}, старт {start}")

            assert_text_is_clean(self, generated["rendered_problem"], seed)


if __name__ == "__main__":
    unittest.main()
