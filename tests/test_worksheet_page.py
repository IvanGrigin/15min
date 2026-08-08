"""Раскладка листочка: страница должна печататься, а не просто собираться.

Проверяется то, из-за чего листочек перестаёт быть листочком: пропало место
под решение, разъехались линейки, условие с угловыми скобками сломало
разметку, страница потянулась за картинкой в сеть. Внешний вид глазами
не проверить, а вот эти свойства — можно.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.web.worksheet_page import (  # noqa: E402
    ROOM_BY_ROLE, render_worksheets, room_for,
)

SHEET = [
    {"role": "счёт", "template_id": "a", "difficulty": "easy",
     "problem": "Вычислите: 2 + 2.", "answer": 4},
    {"role": "уравнение или сравнение", "template_id": "b", "difficulty": "easy",
     "problem": "Найдите x: x + 1 = 3.", "answer": 2},
    {"role": "средняя", "template_id": "c", "difficulty": "medium",
     "problem": "Сколько чисел от 1 до 10 делятся на 3?", "answer": 3},
    {"role": "средняя", "template_id": "d", "difficulty": "medium",
     "problem": "Площадь квадрата с периметром 20 см?", "answer": 25},
    {"role": "трудная", "template_id": "e", "difficulty": "hard",
     "problem": "У кур и коров 10 голов и 28 ног. Сколько коров?", "answer": 4},
]


class LayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = render_worksheets([(SHEET, "09.05.2026")])

    def test_header_has_all_three_fields(self) -> None:
        """Шапка листочка: фамилия, имя и дата — иначе его некому подписать."""
        for field in ("Фамилия", "Имя", "09.05.2026"):
            self.assertIn(field, self.page)

    def test_every_task_is_numbered_and_printed(self) -> None:
        for number, task in enumerate(SHEET, start=1):
            self.assertIn(f'<span class="number">{number}.</span>', self.page)
            self.assertIn(task["problem"], self.page)

    def test_rules_separate_every_task(self) -> None:
        """Линейки: над шапкой, под шапкой, между задачами и под последней."""
        self.assertEqual(self.page.count('class="rule"'), len(SHEET) + 2)

    def test_every_task_gets_room_to_solve(self) -> None:
        """Без доли свободного места задача превращается в строчку списка."""
        weights = [int(value) for value in
                   re.findall(r"flex-grow: (\d+)", self.page)]
        self.assertEqual(len(weights), len(SHEET))
        self.assertTrue(all(weight > 0 for weight in weights))

    def test_hard_task_gets_more_room_than_counting(self) -> None:
        """Сюжетную задачу пишут рассуждением, счётную — в две строки."""
        self.assertGreater(room_for(SHEET[4]), room_for(SHEET[0]))

    def test_every_role_of_the_worksheet_has_a_weight(self) -> None:
        """Роль без веса молча получила бы место по умолчанию."""
        from scripts.make_worksheet import SLOTS
        for role, *_ in SLOTS:
            self.assertIn(role, ROOM_BY_ROLE, f"роли «{role}» не назначен вес")

    def test_page_height_is_fixed_so_the_sheet_fills_the_paper(self) -> None:
        """Без заданной высоты низ страницы остаётся пустым."""
        self.assertIn("height: 277mm", self.page)

    def test_nothing_is_loaded_from_the_network(self) -> None:
        """Листочек печатают, и он обязан выглядеть одинаково без сети."""
        for outside in ("http://", "https://", "//cdn", "<link"):
            self.assertNotIn(outside, self.page)

    def test_angle_brackets_in_a_problem_do_not_break_the_page(self) -> None:
        sheet = [dict(SHEET[0], problem="Сравните: 5 < 7 и <b>10</b> > 2.")]
        page = render_worksheets([(sheet, "01.01.2026")])
        self.assertIn("5 &lt; 7", page)
        self.assertNotIn("<b>10</b>", page)

    def test_brand_column_disappears_without_pictures(self) -> None:
        """Пустая полоса справа читается как обрезанный лист."""
        self.assertIn('class="sheet plain"', self.page)
        self.assertNotIn("<aside", self.page)

    def test_several_sheets_are_split_into_pages(self) -> None:
        page = render_worksheets([(SHEET, "09.05.2026"), (SHEET, "10.05.2026")])
        self.assertEqual(page.count('class="sheet'), 2)
        self.assertIn("page-break-after: always", page)

    def test_key_is_a_separate_page_and_off_by_default(self) -> None:
        """Ключ не должен уехать на лист, который получает ребёнок."""
        self.assertNotIn('<section class="key">', self.page)
        with_key = render_worksheets([(SHEET, "09.05.2026")], with_key=True)
        self.assertIn("Не выдавать вместе с листочком", with_key)
        self.assertIn("page-break-before: always", with_key)
        for task in SHEET:
            self.assertIn(str(task["answer"]), with_key)

    def test_missing_picture_is_reported_not_skipped(self) -> None:
        with self.assertRaises(FileNotFoundError):
            render_worksheets([(SHEET, "09.05.2026")], logo_path="нет-такого.png")


if __name__ == "__main__":
    unittest.main()
