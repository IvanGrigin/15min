import random
import unittest
from unittest.mock import patch
from datetime import date

from problemgen.generation.clock_templates import *
import problemgen.generation.clock_templates as clocks
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.comparison_templates import Character
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules


class ClockTemplateTests(unittest.TestCase):
    def test_source_accounting_and_catalogue(self) -> None:
        manifest = load_source_accounting(); records = manifest["records"]
        numbers = [record["source_problem_number"] for record in records]
        self.assertEqual((manifest["original_numbered_entries"], manifest["removed_duplicates"], len(numbers)), (37, 12, 25))
        self.assertEqual(len(numbers), len(set(numbers))); self.assertEqual(set(numbers), source_problem_numbers())
        templates = load_clock_templates()
        self.assertEqual(len({template["id"] for template in templates}), len(templates))
        self.assertTrue(all(template["answer_type"] == "integer" and template["generation_strategy"] in STRATEGIES for template in templates))
        self.assertTrue(all(record["status"] == "active_template" or len(record["reason"]) > 30 for record in records))

    def test_helper_edges_and_rejections(self) -> None:
        self.assertEqual(seconds_to_time(0), "00:00:00"); self.assertEqual(seconds_to_time(-1), "23:59:59")
        self.assertTrue(clocks._is_all_distinct(1 * 3600 + 23 * 60 + 45)); self.assertFalse(clocks._is_all_distinct(0))
        self.assertTrue(clocks._has_exactly_five_equal(11 * 3600 + 11 * 60 + 10))
        self.assertEqual(backward_tower_meeting(date(2026, 1, 1), 0, date(2026, 1, 2), 0), 12)
        self.assertEqual(drifting_watch_meeting_days(1200, 24), 10); self.assertEqual(cuckoo_strike_count(12), 78); self.assertEqual(reverse_clock_correct_count(), 4)
        with self.assertRaises(ClockTemplateError): nth_display_delta(0, clocks._is_all_distinct, 0, 1)
        with self.assertRaises(ClockTemplateError): drifting_watch_meeting_days(1, 17)

    def test_each_strategy_is_exact_and_reproducible(self) -> None:
        approved = {universe: {character.name for character in characters} for universe, characters in load_approved_characters().items()}
        for template in load_clock_templates():
            for seed in range(20):
                generated = generate_clock_problem(template["id"], seed=seed); self.assertEqual(generated, generate_clock_problem(template["id"], seed=seed)); self.assertIsInstance(generated.answer, int); self.assertNotIn("{", generated.problem_text)
                values = generated.parameters; strategy = template["generation_strategy"]
                if strategy == "all_digits_search":
                    start = sum(part * factor for part, factor in zip(map(int, values["start_time"].split(":")), (3600, 60, 1))); self.assertEqual(generated.answer, nth_display_delta(start, clocks._is_all_distinct, values["ordinal"], values["direction"]))
                elif strategy == "five_equal_digits":
                    start = sum(part * factor for part, factor in zip(map(int, values["start_time"].split(":")), (3600, 60, 1))); self.assertEqual(generated.answer, nth_display_delta(start, clocks._has_exactly_five_equal, 1, values["direction"]))
                elif strategy == "backward_towers": self.assertEqual(generated.answer, backward_tower_meeting(date.fromisoformat(values["first_date"]), values["first_hour"], date.fromisoformat(values["second_date"]), values["second_hour"]))
                elif strategy == "drifting_watches": self.assertEqual(generated.answer, drifting_watch_meeting_days(values["initial_difference"], values["fast_minutes_per_day"] + values["slow_minutes_per_day"]))
                elif strategy == "daily_schedule": self.assertEqual(generated.answer, sum(((hour + values["forward_hours"]) % 24 >= 12) == ((hour - values["backward_hours"]) % 24 >= 12) for hour in range(24)))
                elif strategy == "cuckoo_strikes": self.assertEqual(generated.answer, sum((values["start_hour"] + offset - 1) % 12 + 1 for offset in range(1, 13)))
                else: self.assertEqual(generated.answer, sum((2 * hour) % 12 == 0 for hour in range(values["period_hours"])))
                if template["uses_characters"]: self.assertIn(generated.universe, approved); self.assertTrue(set(generated.characters) <= approved[generated.universe]); self.assertEqual(len(generated.characters), len(set(generated.characters)))

    def test_module_and_site_stack(self) -> None:
        ids = {template["id"] for template in load_clock_templates()}
        for seed in range(100): self.assertIn(generate_clock_problem_from_module(MODULE_ID, rng=random.Random(seed)).template_id, ids)
        modules = ["factors_products_and_factorials", "ratios_fractions_proportions_and_percentages", "combinatorics_and_counting_variants", "pigeonhole_and_guaranteed_selection", "parity_invariants_strategies_and_moves", "number_processes_and_repeated_operations", "calendar_and_weekdays", MODULE_ID]
        worksheet = generate_combined_worksheet_by_modules(modules, seed=721); self.assertEqual(worksheet, generate_combined_worksheet_by_modules(modules, seed=721)); self.assertTrue(all(isinstance(item["answer_value"], int) for item in worksheet["selected_templates"]))

    def test_feminine_character_does_not_receive_masculine_past_tense(self) -> None:
        characters = {"Тестовая вселенная": [Character("Тестовая вселенная", "Нюша", "feminine")]}
        with patch("problemgen.generation.clock_templates.load_approved_characters", return_value=characters):
            for template_id in ("clock_006_cuckoo_strikes", "clock_007_reverse_clock"):
                text = generate_clock_problem(template_id, seed=1).problem_text
                self.assertIn("Нюша", text)
                self.assertNotIn("повернул", text)
                self.assertNotIn("выставил", text)


if __name__ == "__main__": unittest.main()
