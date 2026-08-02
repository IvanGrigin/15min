"""Независимая проверка календарных приёмов из каталога непокрытых задач.

Решатели считают по настоящему календарю, но своим путём: даты складываются
через `datetime`, а дни недели в месяце пересчитываются перебором чисел,
а не формулой шаблона.

Отдельно проверяется корректность самой задачи. Подсказка «в мае пятниц
больше, чем четвергов» задаёт день недели первого мая однозначно, но так
ведут себя лишь 14 пар дней недели из 42: «понедельников больше, чем
четвергов» выполняется при трёх разных вариантах, и ответ на дальнейший
вопрос перестаёт быть единственным. Тест требует, чтобы в условие попадали
только однозначные пары.
"""
from __future__ import annotations

import calendar
import collections
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
SEEDS = range(40)

WEEKDAYS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
GENITIVE = ("понедельников", "вторников", "сред", "четвергов", "пятниц", "суббот", "воскресений")
MONTHS_IN = ("", "январе", "феврале", "марте", "апреле", "мае", "июне",
             "июле", "августе", "сентябре", "октябре", "ноябре", "декабре")
MONTHS_OF = ("", "января", "февраля", "марта", "апреля", "мая", "июня",
             "июля", "августа", "сентября", "октября", "ноября", "декабря")


class MonthWeekdayClueTests(unittest.TestCase):
    TEMPLATE = LIBRARY["month_weekday_clue_date"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            year = generated["parameters"]["found"]

            if "Какой день недели" in text:
                # Другая оболочка: месяц не назван, спрашивают день недели
                # первого числа. Ищем его перебором всех семи вариантов.
                more, less = self.read_clue(text)
                more_index, less_index = GENITIVE.index(more), GENITIVE.index(less)
                fits = [
                    first for first in range(7)
                    # В месяце из 31 дня пять раз встречаются те дни недели,
                    # на которые приходятся 1-е, 2-е и 3-е числа.
                    if ((more_index - first) % 7 < 3) and not ((less_index - first) % 7 < 3)
                ]
                self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
                self.assertEqual(generated["answer_text"], WEEKDAYS[fits[0]],
                                 f"seed {seed}: {text}")
                continue

            clue_month = next(i for i, name in enumerate(MONTHS_IN) if name and name in text)
            more, less = self.read_clue(text)
            more_index, less_index = GENITIVE.index(more), GENITIVE.index(less)

            # Проверяем, что год действительно подходит под подсказку:
            # считаем дни недели в месяце перебором чисел.
            counts: collections.Counter = collections.Counter()
            for day in range(1, calendar.monthrange(year, clue_month)[1] + 1):
                counts[date(year, clue_month, day).weekday()] += 1
            self.assertGreater(
                counts[more_index], counts[less_index],
                f"seed {seed}: год {year} не отвечает подсказке — {text}")

            # Теперь решаем сам вопрос: ищем нужный день недели в нужном месяце.
            # Разбирать нужно только вопрос: в подсказке стоит «вторников
            # больше», и поиск «втор» по всему условию давал второй день
            # вместо третьего. Ошибка была в тесте, не в шаблоне.
            question = text.split(". ", 1)[1]
            asked_weekday = next(i for i, name in enumerate(WEEKDAYS)
                                 if re.search(rf"\b{name}\b", question))
            ask_month = next(i for i, name in enumerate(MONTHS_OF)
                             if name and re.search(rf"{name}\?", question))
            # Искать по обрывку «втор» нельзя: он есть и в «вторник».
            ordinals = {"первый": 1, "первая": 1, "первое": 1,
                        "второй": 2, "вторая": 2, "второе": 2,
                        "третий": 3, "третья": 3, "третье": 3}
            occurrence = next(value for word, value in ordinals.items()
                              if re.search(rf"\b{word}\b", question))
            days = [day for day in range(1, calendar.monthrange(year, ask_month)[1] + 1)
                    if date(year, ask_month, day).weekday() == asked_weekday]
            self.assertEqual(generated["answer"], days[occurrence - 1], f"seed {seed}: {text}")

    def read_clue(self, text: str) -> tuple[str, str]:
        """Пара дней недели из подсказки — в любой из двух оболочек.

        «в январе было сред больше, чем вторников» и «сред было больше,
        чем вторников» — одна и та же подсказка, порядок слов разный.
        """
        found = re.search(r"было (\S+) больше, чем (\S+)\.", text)
        if found is None:
            found = re.search(r"(\S+) было больше, чем (\S+)\.", text)
        return found.groups()

    def test_only_unambiguous_clues_are_used(self) -> None:
        """Иначе ключ печатает один ответ там, где верных несколько."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            more, less = self.read_clue(text)
            more_index, less_index = GENITIVE.index(more), GENITIVE.index(less)

            fits = []
            for first in range(7):
                counts: collections.Counter = collections.Counter()
                for offset in range(31):
                    counts[(first + offset) % 7] += 1
                if counts[more_index] > counts[less_index]:
                    fits.append(first)
            self.assertEqual(
                len(fits), 1,
                f"seed {seed}: подсказка допускает {len(fits)} вариантов — {text}")

    def test_ordinal_agrees_with_the_weekday_gender(self) -> None:
        """«Второй воскресенье» — рассогласование, которое уже случалось."""
        for seed in range(80):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            for wrong in ("первый среда", "второй среда", "третий среда",
                          "первый пятница", "второй пятница", "третий пятница",
                          "первый суббота", "второй суббота", "третий суббота",
                          "первый воскресенье", "второй воскресенье", "третий воскресенье"):
                self.assertNotIn(wrong, text, f"seed {seed}: {text}")
            self.assertNotIn("была первый", text, f"seed {seed}")
            self.assertNotIn("был первая", text, f"seed {seed}")


class DateAfterDaysTests(unittest.TestCase):
    TEMPLATE = LIBRARY["date_after_days"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            day, month_word, year = re.search(r"Сегодня (\d+) (\S+) (\d{4}) года", text).groups()
            offset = int(re.search(r"через (\d+)", text).group(1))
            month = MONTHS_OF.index(month_word)

            moved = date(int(year), month, int(day)) + timedelta(days=offset)
            if "день недели" in text:
                self.assertEqual(generated["answer_text"], WEEKDAYS[moved.weekday()],
                                 f"seed {seed}: {text}")
            else:
                self.assertEqual(generated["answer"], moved.day, f"seed {seed}: {text}")

    def test_weekday_question_states_the_starting_weekday(self) -> None:
        """Иначе задача требует помнить календарь, а не считать."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            if "день недели" not in text:
                continue
            day, month_word, year = re.search(r"Сегодня (\d+) (\S+) (\d{4}) года", text).groups()
            start = date(int(year), MONTHS_OF.index(month_word), int(day))
            self.assertIn(WEEKDAYS[start.weekday()], text, f"seed {seed}: {text}")

    def test_both_questions_occur(self) -> None:
        seen = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add("день недели" in text)
        self.assertEqual(seen, {True, False}, "выпадает только один вопрос")


if __name__ == "__main__":
    unittest.main()
