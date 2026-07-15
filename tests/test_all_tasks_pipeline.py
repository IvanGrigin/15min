from __future__ import annotations

import unittest
from collections import Counter

from problemgen.source_index.all_tasks_pipeline import (
    build_templates,
    build_tree,
    comparable,
    extract_records,
    reconstruct,
    validate_outputs,
)


SAMPLE_CORPUS = """# Все задачи

## sample.pdf

1. Кирилл составляет 11 олимпиады за 3 часа. Сколько олимпиад он составит за 1 час?
2. Натуральные числа от 1 до 120 выписаны подряд. Сколько раз встречается цифра 2?
"""


class AllTasksPipelineTests(unittest.TestCase):
    def test_pipeline_builds_one_template_per_valid_problem(self) -> None:
        records, rejected = extract_records(SAMPLE_CORPUS)
        tree = build_tree(records)
        templates = build_templates(tree)
        stats = validate_outputs(tree, templates, rejected)

        self.assertEqual(stats["valid_problems"], 2)
        self.assertEqual(stats["templates"], 2)
        self.assertEqual(stats["missing_templates"], 0)
        self.assertEqual(stats["duplicates"], 0)
        self.assertEqual(stats["reconstruction_failures"], [])

    def test_repeated_values_reconstruct_source_text(self) -> None:
        records, _ = extract_records(SAMPLE_CORPUS)
        templates = build_templates(build_tree(records))

        for template in templates:
            rebuilt = reconstruct(template["template_text"], template["original_values"])
            self.assertEqual(comparable(rebuilt), comparable(template["source_text"]))

    def test_source_numbers_are_unique_in_sample_tree(self) -> None:
        records, _ = extract_records(SAMPLE_CORPUS)
        tree = build_tree(records)
        source_numbers = [
            problem["source_problem_number"]
            for module in tree["modules"]
            for problem in module["problems"]
        ]

        self.assertEqual(max(Counter(source_numbers).values()), 1)


if __name__ == "__main__":
    unittest.main()
