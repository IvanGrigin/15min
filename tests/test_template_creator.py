from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from problemgen.template_creator.service import TemplateCreatorService
from problemgen.template_creator.storage import TemplateCreatorStore
from problemgen.template_studio.storage import TemplateStudioStore
from problemgen.web.worksheet_site import render_template_creator_page


CONTEXT = {"module_ids": {"sequences_progressions_and_sums"}, "existing_template_ids": set()}


def sequence_candidate() -> dict:
    return {
        "family": "arithmetic_sequence_sum", "module_suggestion": "sequences_progressions_and_sums",
        "strategy_suggestion": "formula", "answer_type": "integer",
        "template_text": "Найдите сумму: {first_term} + {second_term} + {third_term} + … + {last_term}.",
        "parameters": {"first_term": {"type": "positive_integer", "minimum": 1, "maximum": 20}, "difference": {"type": "positive_integer", "minimum": 1, "maximum": 5}, "term_count": {"type": "positive_integer", "minimum": 3, "maximum": 12}},
        "derived": {"second_term": "first_term + difference", "third_term": "first_term + 2 * difference", "last_term": "first_term + difference * (term_count - 1)", "answer": "term_count * (first_term + last_term) // 2"},
        "constraints": ["term_count * (first_term + last_term) % 2 == 0"], "grammar": {"language": "ru"}, "warnings": [], "confidence": {"family": "high"},
    }


class FakeProvider:
    def __init__(self, responses: list[dict]) -> None: self.responses, self.calls = responses, []
    def generate_template(self, problem_text, repository_context, *, repair_errors=None):
        self.calls.append(repair_errors)
        return self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]


class TemplateCreatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.creator_store = TemplateCreatorStore(root / "creator")
        self.active_store = TemplateStudioStore(root / "active")

    def tearDown(self) -> None: self.temp.cleanup()

    def test_page_has_one_problem_input_and_modal(self) -> None:
        page = render_template_creator_page("csrf")
        self.assertIn('id="creator-problem"', page)
        self.assertIn("Создать шаблон", page)
        self.assertIn('id="creator-modal"', page)
        self.assertIn('id="creator-validate"', page)

    def test_no_configured_provider_is_reported_without_fake_fallback(self) -> None:
        service = TemplateCreatorService(None, store=self.creator_store, active_store=self.active_store)
        with self.assertRaisesRegex(ValueError, "не настроен"):
            service.generate("Найдите 2 + 2.", None, CONTEXT)

    def test_non_object_provider_response_is_rejected(self) -> None:
        service = TemplateCreatorService(FakeProvider([[]]), store=self.creator_store, active_store=self.active_store)
        with self.assertRaisesRegex(Exception, "JSON"):
            service.generate("Найдите 2 + 2.", None, CONTEXT)

    def test_provider_creates_complete_json_derived_values_and_previews(self) -> None:
        provider = FakeProvider([sequence_candidate()])
        service = TemplateCreatorService(provider, store=self.creator_store, active_store=self.active_store)
        draft = service.generate("Найдите сумму последовательности: 11 + 14 + 17 + … + 80 + 83.", None, CONTEXT)

        candidate = draft["generated_json"]
        self.assertEqual(draft["status"], "valid")
        self.assertEqual(candidate["family"], "arithmetic_sequence_sum")
        self.assertIn("last_term", candidate["derived"])
        self.assertNotIn("last_term", candidate["parameters"])
        self.assertEqual(len(draft["preview_results"]), 3)
        self.assertTrue(draft["validation_report"]["passed"])

    def test_invalid_provider_response_is_repaired_with_bounded_attempts(self) -> None:
        invalid = sequence_candidate(); invalid["parameters"] = {}
        provider = FakeProvider([invalid, sequence_candidate()])
        service = TemplateCreatorService(provider, store=self.creator_store, active_store=self.active_store)
        draft = service.generate("Найдите сумму последовательности.", None, CONTEXT)
        self.assertTrue(draft["validation_report"]["passed"])
        self.assertEqual(draft["repair_attempts"], 1)
        self.assertTrue(provider.calls[1])

    def test_repair_limit_and_missing_strategy_block_activation(self) -> None:
        invalid = sequence_candidate(); invalid["strategy_suggestion"] = "new_unimplemented_strategy"
        provider = FakeProvider([invalid])
        service = TemplateCreatorService(provider, store=self.creator_store, active_store=self.active_store)
        draft = service.generate("Найдите сумму последовательности.", None, CONTEXT)
        self.assertFalse(draft["validation_report"]["passed"])
        self.assertEqual(draft["repair_attempts"], 3)
        with self.assertRaises(ValueError): service.activate(draft["draft_id"], CONTEXT)

    def test_unsafe_expression_and_incomplete_name_grammar_are_rejected(self) -> None:
        unsafe = sequence_candidate()
        unsafe["derived"]["answer"] = "first_term.__class__"
        service = TemplateCreatorService(FakeProvider([unsafe]), store=self.creator_store, active_store=self.active_store)
        draft = service.generate("Найдите сумму последовательности.", None, CONTEXT)
        self.assertFalse(draft["validation_report"]["passed"])
        self.assertTrue(any(check["id"] == "expressions" and not check["passed"] for check in draft["validation_report"]["checks"]))

        named = sequence_candidate()
        named["parameters"]["author"] = {"type": "name", "allowed_values": ["Аня"]}
        named["template_text"] += " {author} записал задачу."
        service = TemplateCreatorService(FakeProvider([named]), store=self.creator_store, active_store=self.active_store)
        draft = service.generate("Аня записала задачу.", None, CONTEXT)
        self.assertFalse(draft["validation_report"]["passed"])
        self.assertTrue(any(check["id"] == "schema" and not check["passed"] for check in draft["validation_report"]["checks"]))

    def test_activation_regeneration_history_and_deletion(self) -> None:
        provider = FakeProvider([sequence_candidate(), sequence_candidate()])
        service = TemplateCreatorService(provider, store=self.creator_store, active_store=self.active_store)
        draft = service.generate("Найдите сумму последовательности.", None, CONTEXT)
        regenerated = service.regenerate(draft["draft_id"], CONTEXT)
        self.assertTrue(any(event["action"] == "regenerated" for event in regenerated["revision_history"]))
        active = service.activate(draft["draft_id"], CONTEXT)
        self.assertEqual(active["status"], "active")
        self.assertEqual(len(self.active_store.load_active_templates()), 1)
        with self.assertRaises(ValueError): service.delete(draft["draft_id"], confirmed=True)
        second = service.generate("Найдите сумму последовательности ещё раз.", None, CONTEXT)
        service.delete(second["draft_id"], confirmed=True)
        with self.assertRaises(KeyError): self.creator_store.load_draft(second["draft_id"])


if __name__ == "__main__": unittest.main()
