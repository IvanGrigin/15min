"""Батч Б3: календарь и наибольшая сумма цифр.

Решатели ничего не берут из шаблонов. Календарные ответы проверяются
настоящим календарём: даты перебираются по годам через `datetime.date`,
а не по формуле сдвигов. Наибольшая сумма цифр пересчитывается прямым
перебором отрезка — медленно, зато без всяких догадок о том, где стоят
девятки.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)
SPACE = "[\\s ]+"
MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря")
WEEKDAYS = {"понедельник": 0, "вторник": 1, "четверг": 3,
            "пятницу": 4, "субботу": 5, "воскресенье": 6}


class LargestDigitSumTests(unittest.TestCase):
    TEMPLATE = LIBRARY["largest_digit_sum_in_range"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high = (int(value) for value in
                         re.search(r"от (\d+) до (\d+)", text).groups())

            # Решение с нуля: перебираем весь отрезок и складываем цифры.
            # Никаких догадок про девятки — только прямой счёт.
            best_sum, best_value, count = -1, None, 0
            for value in range(low, high + 1):
                total = sum(int(digit) for digit in str(value))
                if total > best_sum:
                    best_sum, best_value, count = total, value, 1
                elif total == best_sum:
                    count += 1
            self.assertEqual(count, 1, f"seed {seed}: ответ не единственный — {text}")
            expected = best_sum if "сумма цифр может быть" in text else best_value
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class LastWeekdayTests(unittest.TestCase):
    TEMPLATE = LIBRARY["last_weekday_day_of_year"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # Месяц берётся из оборота «последний четверг марта», а не поиском
            # по всему тексту: в условии есть пример «1 февраля — 32-й день года»,
            # и он перехватывал разбор.
            occasion = re.search(r"в (предпоследн\w+|последн\w+) (\S+) ([а-я]+)", text)
            weekday = WEEKDAYS[occasion.group(2)]
            month = MONTHS.index(occasion.group(3)) + 1
            step_back = 7 if occasion.group(1).startswith("предпоследн") else 0

            # Решение с нуля: проходим сорок настоящих лет и для каждого
            # находим нужный день календарём, а не формулой.
            numbers = set()
            for year in range(2020, 2060):
                day = 31
                while True:
                    try:
                        found = date(year, month, day)
                    except ValueError:
                        day -= 1
                        continue
                    break
                while found.weekday() != weekday:
                    found -= timedelta(days=1)
                found -= timedelta(days=step_back)
                numbers.add(found.timetuple().tm_yday)

            if "Сколько разных номеров" in text:
                expected = max(numbers) - min(numbers) + 1
            elif "наибольший" in text:
                expected = max(numbers)
            else:
                expected = min(numbers)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class SameWeekdayLaterTests(unittest.TestCase):
    TEMPLATE = LIBRARY["same_weekday_years_later"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            day = int(re.search(r"(\d+) [а-я]+ \d{4} года", text).group(1))
            month = next(index for index, name in enumerate(MONTHS, 1) if name in text)
            year = int(re.search(r"(\d{4}) года", text).group(1))

            # Решение с нуля: год за годом смотрим настоящий календарь.
            weekday = date(year, month, day).weekday()
            ahead = next(step for step in range(1, 30)
                         if date(year + step, month, day).weekday() == weekday)
            expected = year + ahead if "В каком ближайшем году" in text else ahead
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_gap_is_not_always_the_same(self) -> None:
        """Ответ обязан меняться, иначе задача решается угадыванием."""
        seen = {generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]["gap"]
                for seed in range(60)}
        self.assertGreater(len(seen), 1, "разрыв всегда один и тот же")


class VacationDaysTests(unittest.TestCase):
    TEMPLATE = LIBRARY["days_of_vacation_between_dates"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            start_day = int(re.search(r"в отпуск (\d+)", text).group(1))
            start_month = next(index for index, name in enumerate(MONTHS, 1)
                               if f"отпуск {start_day} {name}" in text)

            # Решение с нуля: шагаем по календарю невисокосного года по дню.
            start = date(2025, start_month, start_day)
            if "Какого числа" in text:
                length = int(re.search(rf"в отпуске (\d+){SPACE}д", text).group(1))
                expected = (start + timedelta(days=length + 1)).day
            else:
                end_day = int(re.search(r"на работу (\d+)", text).group(1))
                end_month = next(index for index, name in enumerate(MONTHS, 1)
                                 if f"работу {end_day} {name}" in text)
                end = date(2025, end_month, end_day)
                expected = (end - start).days - 1
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
