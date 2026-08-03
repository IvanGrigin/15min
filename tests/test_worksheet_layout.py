"""Проверка раскладки пятнадцатиминутки.

Правило разобрано по листочкам преподавателя (docs/WORKSHEET_FORMAT.md):
первое место — счёт, второе — уравнение или сравнение, дальше две средние
и одна трудная. Балл считается как «решённые плюс один», поэтому две задачи
обязаны быть посильными, а на отличную оценку должна требоваться трудная.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.make_worksheet import (  # noqa: E402
    COUNTING_MODULES, EQUATION_MODULES, build, difficulty_of, teacher_difficulty,
)
from scripts.seed_worksheet_templates import load_library  # noqa: E402

TEMPLATES = load_library()
MARKED = teacher_difficulty()
SEEDS = range(12)


class WorksheetLayoutTests(unittest.TestCase):
    def sheets(self):
        for seed in SEEDS:
            yield seed, build(TEMPLATES, random.Random(seed), MARKED)

    def test_five_tasks_with_the_promised_shape(self) -> None:
        for seed, sheet in self.sheets():
            self.assertEqual(len(sheet), 5, f"seed {seed}")
            levels = [task["difficulty"] for task in sheet]
            self.assertEqual(levels[4], "hard", f"seed {seed}: последняя не трудная — {levels}")
            self.assertLessEqual(levels.count("hard"), 2,
                                 f"seed {seed}: трудных слишком много — {levels}")
            # Две задачи обязаны быть по силам: без них четвёрка недостижима.
            self.assertGreaterEqual(sum(1 for level in levels if level != "hard"), 3,
                                    f"seed {seed}: посильных мало — {levels}")

    def test_first_place_is_counting(self) -> None:
        for seed, sheet in self.sheets():
            self.assertIn(sheet[0]["module_id"], COUNTING_MODULES,
                          f"seed {seed}: на первом месте не счёт")
            self.assertEqual(sheet[0]["difficulty"], "easy", f"seed {seed}")

    def test_second_place_is_equation_or_comparison(self) -> None:
        for seed, sheet in self.sheets():
            self.assertIn(sheet[1]["module_id"], EQUATION_MODULES, f"seed {seed}")

    def test_topics_never_repeat(self) -> None:
        for seed, sheet in self.sheets():
            modules = [task["module_id"] for task in sheet]
            self.assertEqual(len(set(modules)), 5, f"seed {seed}: темы повторились — {modules}")

    def test_every_task_is_rendered_and_answered(self) -> None:
        for seed, sheet in self.sheets():
            for number, task in enumerate(sheet, start=1):
                self.assertNotIn("{", task["problem"], f"seed {seed}, задача {number}")
                self.assertTrue(task["problem"].rstrip().endswith(("?", ".", "!")),
                                f"seed {seed}, задача {number}: {task['problem'][-40:]}")
                self.assertNotEqual(str(task["answer"]).strip(), "",
                                    f"seed {seed}, задача {number}: пустой ответ")

    def test_teacher_marks_win_over_own_guess(self) -> None:
        """Оценка из смотра важнее собственной: её ставил человек."""
        marked_hard = [t for t in TEMPLATES if MARKED.get(t["template_id"]) == "easy"
                       and (t.get("math_notes") or {}).get("level") == "advanced"]
        for template in marked_hard:
            self.assertEqual(difficulty_of(template, MARKED), "easy",
                             f"{template['template_id']}: оценка преподавателя проиграла")


if __name__ == "__main__":
    unittest.main()
