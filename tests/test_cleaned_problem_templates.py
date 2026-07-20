from __future__ import annotations

import random
import unittest

from problemgen.catalog.problem_templates import load_template_catalog, list_modules
from problemgen.generation.template_generator import generate_problem_from_template
from problemgen.source_index.cleaned_problem_templates import (
    SOURCE_PATH,
    parse_cleaned_problems,
    validate_current_catalog,
)


class CleanedProblemTemplatesTests(unittest.TestCase):
    def test_source_problem_count_matches_template_count(self) -> None:
        stats = validate_current_catalog()

        self.assertEqual(stats["source_count"], 1528)
        self.assertEqual(stats["template_count"], len(load_template_catalog()))
        self.assertLess(stats["template_count"], stats["source_count"])
        self.assertEqual(stats["errors"], [])

    def test_catalog_loads_through_existing_loader(self) -> None:
        templates = load_template_catalog()

        self.assertGreaterEqual(len(templates), 8)
        self.assertEqual(len({template["template_id"] for template in templates}), len(templates))

    def test_modules_have_russian_names(self) -> None:
        modules = list_modules()

        self.assertGreaterEqual(len(modules), 8)
        self.assertTrue(all(any("А" <= char <= "я" or char == "ё" for char in module["title"]) for module in modules))

    def test_worksheet_generator_can_generate_five_problem_samples(self) -> None:
        modules = list_modules()[:5]
        problems = [
            generate_problem_from_template(module["id"], module["available_difficulties"][0], rng=random.Random(index), index=index)
            for index, module in enumerate(modules, start=1)
        ]

        self.assertEqual(len(problems), 5)
        self.assertTrue(all(problem.problem_text for problem in problems))
        self.assertTrue(all("{" not in problem.problem_text for problem in problems))

    def test_markdown_parser_skips_headings(self) -> None:
        problems = parse_cleaned_problems(SOURCE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(problems[0]["source_problem_number"], 1)
        self.assertNotIn("##", problems[0]["text"])


if __name__ == "__main__":
    unittest.main()
