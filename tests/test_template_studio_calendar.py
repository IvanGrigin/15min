"""Независимая проверка шаблонов темы «Календарь и дни недели».

Каждый решатель решает задачу по её условию с нуля, а не повторяет формулы
шаблона: НОК считается через math.lcm; трамваи — через отдельно записанное
уравнение «время оборота постоянно»; школьный день — через уравнение бюджета
времени, решённое относительно короткой перемены; занятия дважды в неделю —
явной симуляцией дат посещения через чередующиеся зазоры, а не закрытой формулой.
"""
from __future__ import annotations

import math
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
FRIENDS = LIBRARY["friends_periodic_meeting_lcm"]
TRAMS = LIBRARY["tram_interval_change"]
SCHOOL_DAY = LIBRARY["school_day_short_break"]
LAST_VISIT = LIBRARY["weekday_lesson_last_visit"]
SEEDS = range(25)


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый плейсхолдер")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: текст должен начинаться с заглавной")
    case.assertIn(text[-1], ".?!", f"seed {seed}: текст должен заканчиваться знаком препинания")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ не должен быть в условии")


class FriendsPeriodicMeetingTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(FRIENDS, random.Random(seed))
            values = generated["parameters"]
            a, b, c = values["a"], values["b"], values["c"]

            expected = math.lcm(a, b, c)

            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_answer_exceeds_every_period(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(FRIENDS, random.Random(seed))
            values = generated["parameters"]
            for key in ("a", "b", "c"):
                self.assertGreater(generated["answer"], values[key], f"seed {seed}")
            self.assertLessEqual(generated["answer"], 180, f"seed {seed}")


class TramIntervalChangeTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(TRAMS, random.Random(seed))
            values = generated["parameters"]
            n1, t1, delta, action = values["n1"], values["t1"], values["delta"], values["action"]

            # Решение с нуля: время полного оборота круга не зависит от числа
            # трамваев на линии — это физическая константа маршрута, а не
            # формула из шаблона. Восстанавливаем её из вчерашних данных и
            # делим на сегодняшнее число трамваев.
            loop_minutes = n1 * t1
            # action несёт предлог вместе с глаголом («на маршрут добавили» /
            # «с маршрута убрали»), поэтому смотрим на глагол внутри строки,
            # а не сравниваем её целиком: формулировка может смениться.
            self.assertIn(action.split()[-1], {"добавили", "убрали"}, f"seed {seed}: {action!r}")
            n2 = n1 + delta if action.endswith("добавили") else n1 - delta
            self.assertGreaterEqual(n2, 2, f"seed {seed}: трамваев должно остаться хотя бы 2")
            self.assertEqual(loop_minutes % n2, 0, f"seed {seed}: интервал обязан быть целым")
            expected = loop_minutes // n2

            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_interval_actually_changed(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(TRAMS, random.Random(seed))
            values = generated["parameters"]
            self.assertNotEqual(generated["answer"], values["t1"], f"seed {seed}")


class SchoolDayShortBreakTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(SCHOOL_DAY, random.Random(seed))
            values = generated["parameters"]
            L = values["L"]
            lesson_min = values["lesson_min"]
            big = values["big"]
            before = values["before"]
            after = values["after"]

            # Решение с нуля: составляем бюджет времени «от прихода до ухода»
            # как сумму пяти слагаемых и решаем его относительно короткой
            # перемены, а не подглядываем derived_values шаблона. total_span
            # достаём из текста регуляркой (числа в тексте идут в порядке
            # L, lesson_min, big, before, after, total_span), а не из
            # generated["parameters"], где его нет — total_span derived.
            # Разница между приходом и уходом в условии больше не написана —
            # её, как и ребёнок, считаем сами по двум моментам времени.
            rendered = generated["rendered_problem"]
            arrive, leave = re.findall(r"в (\d{2}):(\d{2})", rendered)
            total_span = ((int(leave[0]) * 60 + int(leave[1]))
                          - (int(arrive[0]) * 60 + int(arrive[1])))
            short_breaks_count = L - 2
            self.assertGreater(short_breaks_count, 0, f"seed {seed}")
            remaining = total_span - before - after - L * lesson_min - big
            self.assertEqual(remaining % short_breaks_count, 0, f"seed {seed}")
            expected = remaining // short_breaks_count

            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            self.assertGreater(expected, 0, f"seed {seed}")
            self.assertLess(expected, big, f"seed {seed}: короткая перемена короче большой")
            assert_text_is_clean(self, generated["rendered_problem"], seed)


class WeekdayLessonLastVisitTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(LAST_VISIT, random.Random(seed))
            values = generated["parameters"]
            rendered = generated["rendered_problem"]

            # Решение с нуля: не используем закрытую формулу D1+7+r. Достаём
            # обе даты посещения и порог из текста (три числа в тексте идут
            # в порядке D1, D2, порог — regex вместо чтения derived_values),
            # затем честно строим цепочку дат вперёд от первой, чередуя два
            # зазора (r и 7-r), пока не найдём вторую дату из текста — это
            # подтверждает, какой зазор первый, а какой второй. После этого
            # ищем последнее посещение из цепочки строго до порога.
            numbers = [int(tok) for tok in re.findall(r"\d+", rendered)]
            self.assertEqual(len(numbers), 3, f"seed {seed}: в тексте должно быть ровно 3 числа")
            d1, d2, threshold = numbers

            gap = d2 - d1
            r = gap % 7
            self.assertNotEqual(r, 0, f"seed {seed}: зазор не может быть кратен неделе")
            gap_other = 7 - r

            visits = [d1]
            gaps = [r, gap_other]
            i = 0
            while visits[-1] < d2:
                visits.append(visits[-1] + gaps[i % 2])
                i += 1
            self.assertEqual(visits[-1], d2, f"seed {seed}: цепочка обязана дойти ровно до второй даты")

            before_threshold = [v for v in visits if v < threshold]
            self.assertTrue(before_threshold, f"seed {seed}: должен быть хотя бы один визит раньше порога")
            expected = max(before_threshold)

            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, rendered, seed)

    def test_answer_render_has_no_grammatically_agreed_month(self) -> None:
        # Ответ — голое число: месяц у дат стоит в родительном падеже
        # единственного числа независимо от дня, а не по счётному
        # согласованию 1/2-4/5+, поэтому unit/unit_param в answer_rendering
        # не используются вовсе (см. math_notes.grammar_trap шаблона).
        self.assertNotIn("unit", LAST_VISIT["answer_rendering"]["parts"][0])
        self.assertNotIn("unit_param", LAST_VISIT["answer_rendering"]["parts"][0])


if __name__ == "__main__":
    unittest.main()
