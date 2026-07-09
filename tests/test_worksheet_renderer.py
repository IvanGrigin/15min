from __future__ import annotations

import unittest
from pathlib import Path

from problemgen.io.worksheet_renderer import (
    WorksheetRenderError,
    build_worksheet_plan,
    load_problem_source,
    load_problem_texts,
    load_worksheet_template,
    prepare_problem_text,
)


class WorksheetRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = Path(__file__).resolve().parents[1]
        self.template_path = self.project_root / "data" / "templates" / "worksheets" / "worksheet_5_tasks.json"

    def test_template_loads_with_five_slots(self) -> None:
        template = load_worksheet_template(self.template_path)
        self.assertEqual(template["id"], "worksheet_5_tasks")
        self.assertEqual(len(template["problem_area"]["slots"]), 5)

    def test_problem_loader_supports_bundle_format(self) -> None:
        problems_path = self.project_root / "outputs" / "generated" / "counting.json"
        problems = load_problem_texts(problems_path)
        self.assertEqual(len(problems), 5)
        self.assertTrue(problems[0])

    def test_problem_source_reads_header_from_example_file(self) -> None:
        problems_path = self.project_root / "outputs" / "generated" / "worksheet_5_math_problems_example.json"
        source = load_problem_source(problems_path)
        self.assertEqual(source.header["surname"], "Иванов")
        self.assertEqual(source.header["name"], "Миша")
        self.assertEqual(source.header["date"], "09.07.2026")
        self.assertEqual(len(source.problems), 5)

    def test_problem_loader_supports_plain_list_format(self) -> None:
        problems_path = self.project_root / "outputs" / "friendship_class" / "1000_zadach.json"
        problems = load_problem_texts(problems_path)
        self.assertGreater(len(problems), 10)
        self.assertTrue(problems[0].startswith("1."))

    def test_prepare_problem_text_renumbers_input(self) -> None:
        text = prepare_problem_text("7. Старая нумерация не должна остаться.", 2)
        self.assertEqual(text, "2. Старая нумерация не должна остаться.")

    def test_plan_raises_clear_error_when_problem_count_mismatches(self) -> None:
        template = load_worksheet_template(self.template_path)
        with self.assertRaises(WorksheetRenderError) as error:
            build_worksheet_plan(
                template,
                ["Одна задача"],
                measure=lambda text, font_size, bold: len(text) * 8,
            )
        self.assertIn("Шаблон ожидает 5 задач", str(error.exception))

    def test_plan_raises_clear_error_when_text_overflows_slot(self) -> None:
        template = load_worksheet_template(self.template_path)
        huge_problem = " ".join(["длинныйтекст"] * 120)
        with self.assertRaises(WorksheetRenderError) as error:
            build_worksheet_plan(
                template,
                [huge_problem] * 5,
                measure=lambda text, font_size, bold: len(text) * 12,
            )
        self.assertIn("не помещается в слот", str(error.exception))


if __name__ == "__main__":
    unittest.main()
