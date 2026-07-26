from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from problemgen.template_studio.analyzer import TemplateAnalyzer
from problemgen.template_studio.safe_expressions import SafeExpressionError, evaluate_expression
from problemgen.template_studio.service import TemplateStudioService
from problemgen.template_studio.storage import TemplateStudioStore


KNOWN_MODULES = {"arithmetic", "sequences_progressions_and_sums"}


class TemplateStudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = TemplateStudioStore(Path(self.temporary.name) / "template_studio")
        self.service = TemplateStudioService(store=self.store)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _draft(self, *, template_id: str = "studio_sum_001") -> dict:
        draft = self.service.create_from_analysis({
            "original_text": "Найдите сумму 11 + 14.",
            "module_id": "arithmetic",
            "source_problem_number": "1",
            "source_filename": "manual.md",
        })
        return self.service.update_draft(draft["draft_id"], {
            "template_id": template_id,
            "module_id": "arithmetic",
            "candidate_template_text": "Найдите сумму чисел {a} и {b}.",
            "answer_type": "integer",
            "parameter_schema": {
                "a": {"type": "positive_integer", "minimum": 1, "maximum": 20},
                "b": {"type": "positive_integer", "minimum": 1, "maximum": 20},
            },
            "derived_values": {"total": "a + b"},
            "solver_strategy": "formula",
            "answer_expression": "total",
            "answer_rendering": {"type": "integer"},
            "grammar_metadata": {},
            "constraints": {},
            "source_metadata": {"problem_number": "1", "filename": "manual.md"},
            "notes": "Тестовый шаблон.",
            "language": "ru",
        })

    def test_analysis_creates_draft_and_detects_numbers_name_and_operations(self) -> None:
        draft = self.service.create_from_analysis({"original_text": "Иван нашёл 12 + 5 см.", "module_id": "arithmetic"})

        self.assertEqual(draft["status"], "draft")
        self.assertEqual(draft["analysis"]["detected_numbers"], ["12", "5"])
        self.assertIn("Иван", draft["analysis"]["detected_names"])
        self.assertIn("сложение", draft["analysis"]["detected_operations"])
        self.assertTrue((self.store.drafts_root / f"{draft['draft_id']}.json").is_file())

    def test_unsupported_problem_becomes_partial_draft(self) -> None:
        draft = self.service.create_from_analysis({"original_text": "Докажите, что фигура имеет ось симметрии."})

        self.assertEqual(draft["status"], "draft")
        self.assertTrue(draft["analysis"]["warnings"])
        self.assertTrue(draft["analysis"]["unsupported_features"])

    def test_detected_sequence_can_validate_as_an_integer_template(self) -> None:
        draft = self.service.create_from_analysis({
            "original_text": "Найдите сумму последовательности: 11 + 14 + 17 + … + 80 + 83.",
            "module_id": "sequences_progressions_and_sums",
        })

        report = self.service.validate(
            draft["draft_id"],
            known_module_ids=KNOWN_MODULES,
            existing_template_ids=set(),
        )

        self.assertTrue(report["passed"])
        self.assertEqual(report["successful_examples"], 10)

    def test_edit_preview_and_seed_are_deterministic(self) -> None:
        draft = self._draft()
        first = self.service.preview(draft["draft_id"], count=3, seed=44)
        second = self.service.preview(draft["draft_id"], count=3, seed=44)

        self.assertEqual(first["previews"], second["previews"])
        self.assertTrue(all(item["validation"]["passed"] for item in first["previews"]))
        self.assertIn("derived_values", first["previews"][0])

    def test_safe_expression_rejects_arbitrary_code(self) -> None:
        self.assertEqual(evaluate_expression("gcd(a, b) + factorial(3)", {"a": 12, "b": 8}), 10)
        with self.assertRaises(SafeExpressionError):
            evaluate_expression("__import__('os').system('whoami')", {})
        with self.assertRaises(SafeExpressionError):
            evaluate_expression("a.__class__", {"a": 1})

    def test_fraction_parameter_stays_exact_until_json_boundary(self) -> None:
        draft = self._draft(template_id="studio_fraction_001")
        draft = self.service.update_draft(draft["draft_id"], {
            "candidate_template_text": "Увеличьте дробь {part} в два раза.",
            "parameter_schema": {"part": {"type": "fraction", "minimum": 1, "maximum": 3}},
            "derived_values": {"double_part": "part * 2"},
            "answer_expression": "double_part",
            "answer_type": "fraction",
        })
        previews = self.service.preview(draft["draft_id"], count=1, seed=3)["previews"]

        self.assertTrue(previews[0]["validation"]["passed"])
        self.assertIsInstance(previews[0]["derived_values"]["double_part"], (int, str))

    def test_validation_activation_and_atomic_overlay(self) -> None:
        draft = self._draft()
        report = self.service.validate(draft["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())
        self.assertTrue(report["passed"])
        active = self.service.activate(draft["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())

        self.assertEqual(active["status"], "active")
        self.assertEqual(self.store.load_active_templates()[0]["template_id"], "studio_sum_001")
        with self.store.active_catalogue_path.open(encoding="utf-8") as source:
            self.assertEqual(json.load(source)["templates"][0]["template_id"], "studio_sum_001")
        self.assertTrue(list(self.store.history_root.glob("catalogue_before_*.json")))

    def test_duplicate_id_division_by_zero_integer_enforcement_and_placeholder_are_rejected(self) -> None:
        duplicate = self._draft(template_id="already_used")
        duplicate_report = self.service.validate(duplicate["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids={"already_used"})
        self.assertFalse(duplicate_report["passed"])
        self.assertIn("template_id", {item["id"] for item in duplicate_report["checks"] if not item["passed"]})

        invalid = self._draft(template_id="studio_division_001")
        invalid = self.service.update_draft(invalid["draft_id"], {
            "candidate_template_text": "Разделите {a} на {b}.",
            "parameter_schema": {"a": {"type": "integer", "minimum": 1, "maximum": 3}, "b": {"type": "integer", "minimum": 0, "maximum": 1}},
            "derived_values": {}, "answer_expression": "a / b", "answer_type": "integer",
        })
        report = self.service.validate(invalid["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())
        self.assertFalse(report["passed"])
        self.assertIn("examples", {item["id"] for item in report["checks"] if not item["passed"]})

        unresolved = self._draft(template_id="studio_placeholder_001")
        unresolved = self.service.update_draft(unresolved["draft_id"], {"candidate_template_text": "Найдите {missing}.", "parameter_schema": {"a": {"type": "integer", "minimum": 1, "maximum": 2}}, "derived_values": {}, "answer_expression": "a"})
        report = self.service.validate(unresolved["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())
        self.assertFalse(report["passed"])
        self.assertIn("placeholders", {item["id"] for item in report["checks"] if not item["passed"]})

    def test_delete_active_archive_and_restore_lifecycle(self) -> None:
        draft = self._draft()
        with self.assertRaises(ValueError):
            self.service.delete_draft(draft["draft_id"], confirmed=False)
        self.service.validate(draft["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())
        active = self.service.activate(draft["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())
        with self.assertRaises(ValueError):
            self.service.delete_draft(active["draft_id"], confirmed=True)
        archived = self.service.archive(active["draft_id"])
        self.assertEqual(archived["status"], "archived")
        self.assertEqual(self.store.load_active_templates(), [])
        restored = self.service.restore(active["draft_id"], known_module_ids=KNOWN_MODULES, existing_template_ids=set())
        self.assertEqual(restored["status"], "active")

    def test_active_template_is_served_by_the_studio_site(self) -> None:
        """Опубликованный шаблон доходит до сайта, а ответ не утекает в условие."""
        from problemgen.web import studio_site

        template = {
            "template_id": "studio_site_001", "module_id": "arithmetic",
            "candidate_template_text": "Найдите сумму {a} и {b}.",
            "parameter_schema": {"a": {"type": "integer", "min": 2, "max": 2},
                                 "b": {"type": "integer", "min": 3, "max": 3}},
            "derived_values": {}, "constraints": [], "answer_expression": "a + b",
            "answer_type": "integer", "answer_rendering": {"type": "integer"},
            "grammar_metadata": {}, "source_metadata": {"problem_number": "test"},
            "solver_strategy": "formula",
        }
        with patch.object(studio_site, "active_templates", return_value=[template]):
            modules = studio_site.available_modules()
            self.assertEqual([item["module_id"] for item in modules], ["arithmetic"])
            worksheet = studio_site.generate_worksheet(task_count=2, seed=1)

        for task in worksheet["tasks"]:
            self.assertEqual(task["template_id"], "studio_site_001")
            self.assertEqual(task["answer_value"], 5)
            self.assertNotIn("5", task["problem"])
        self.assertEqual(worksheet["source"], "template_studio_library")


if __name__ == "__main__":
    unittest.main()
