"""Машинные проверки словаря существительных.

Эти правила русского языка выполняются без исключений, поэтому их нарушение —
всегда опечатка в данных. Проверки нужны потому, что словарь пополняется
массово (в том числе локальной моделью), и человек не перечитывает 12 форм
на каждое слово.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

NOUNS_PATH = PROJECT_ROOT / "data" / "language" / "nouns" / "russian_nouns.json"
CASES = ("nom", "gen", "dat", "acc", "ins", "pre",
         "nom_pl", "gen_pl", "dat_pl", "acc_pl", "ins_pl", "pre_pl")
VELAR_AND_HUSHING = "кгхжшчщ"


def load_nouns() -> dict:
    return json.loads(NOUNS_PATH.read_text(encoding="utf-8"))["nouns"]


class NounDictionaryIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nouns = load_nouns()

    def test_every_word_has_twelve_non_empty_forms(self) -> None:
        for word, entry in self.nouns.items():
            forms = entry["forms"]
            for case in CASES:
                self.assertIn(case, forms, f"{word}: нет формы {case}")
                self.assertTrue(str(forms[case]).strip(), f"{word}: пустая форма {case}")
                self.assertEqual(forms[case], forms[case].strip(), f"{word}: пробелы в форме {case}")

    def test_accusative_plural_follows_animacy(self) -> None:
        """Винительный мн.: у одушевлённых = родительный, у неодушевлённых = именительный.

        Правило без исключений. Именно на нём поймались «голова: acc_pl=голов»
        и неверно проставленная одушевлённость у оленя и пчелы.
        """
        for word, entry in self.nouns.items():
            forms = entry["forms"]
            expected = forms["gen_pl"] if entry.get("animate") else forms["nom_pl"]
            self.assertEqual(
                forms["acc_pl"], expected,
                f"{word}: acc_pl={forms['acc_pl']!r}, а при animate={entry.get('animate', False)} "
                f"должно быть {expected!r}",
            )

    def test_no_y_after_velars_and_hushing(self) -> None:
        """После к, г, х, ж, ш, ч, щ пишется -и, а не -ы. Орфография без исключений."""
        for word, entry in self.nouns.items():
            for case in ("gen", "nom_pl", "acc_pl"):
                value = entry["forms"][case]
                if len(value) > 1 and value.endswith("ы"):
                    self.assertNotIn(
                        value[-2], VELAR_AND_HUSHING,
                        f"{word}.{case}={value!r}: после {value[-2]!r} пишется -и",
                    )

    def test_declinable_words_actually_decline(self) -> None:
        """Если все 12 форм совпали — это несклоняемое слово, и такие есть.

        Но совпадение именительного и родительного единственного при разном
        множественном почти всегда означает копирование формы не в ту ячейку.
        """
        for word, entry in self.nouns.items():
            forms = entry["forms"]
            singular = {forms[case] for case in CASES[:6]}
            plural = {forms[case] for case in CASES[6:]}
            if len(singular) == 1 and len(plural) == 1:
                continue  # несклоняемое: лье, хачапури
            self.assertGreater(
                len(singular | plural), 2,
                f"{word}: слово объявлено склоняемым, но форм почти нет",
            )

    def test_count_forms_override_has_three_entries(self) -> None:
        for word, entry in self.nouns.items():
            override = entry.get("count_forms")
            if override is None:
                continue
            self.assertEqual(len(override), 3, f"{word}: count_forms должен содержать ровно три формы")
            for form in override:
                self.assertTrue(str(form).strip(), f"{word}: пустая форма в count_forms")

    def test_gender_and_flags_are_well_formed(self) -> None:
        for word, entry in self.nouns.items():
            self.assertIn(entry["gender"], {"m", "f", "n"}, word)
            self.assertIsInstance(entry.get("animate", False), bool, word)
            self.assertIsInstance(entry.get("countable", True), bool, word)


if __name__ == "__main__":
    unittest.main()
