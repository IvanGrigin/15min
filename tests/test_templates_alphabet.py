"""Независимо проверяет JSON-шаблоны скрытого алфавитного порядка."""
from __future__ import annotations

import itertools
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
SEEDS = range(25)
LETTERS = "ИВАН"


def words_without_repetitions(order: tuple[str, ...]) -> list[str]:
    """Строит все перестановки и сортирует их по проверяемому алфавиту."""
    return sorted(("".join(word) for word in itertools.permutations(LETTERS)), key=lambda word: tuple(order.index(letter) for letter in word))


def words_with_repetitions(order: tuple[str, ...]) -> list[str]:
    """Строит слова с повторениями в том же лексикографическом порядке."""
    return sorted(("".join(word) for word in itertools.product(LETTERS, repeat=4)), key=lambda word: tuple(order.index(letter) for letter in word))


class AlphabetTemplatesTests(unittest.TestCase):
    """Восстанавливает скрытый порядок полным перебором 24 алфавитов."""

    def check(self, template_id: str, repeated: bool, expected_position: int | None) -> None:
        """Ищет единственный порядок, согласованный с напечатанной подсказкой."""
        template = LIBRARY[template_id]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            text = generated["rendered_problem"]
            printed = re.findall(r"[ИВАН]{4}", text)
            self.assertGreaterEqual(len(printed), 1, f"seed {seed}: {text}")
            clue = printed[0]
            word_lists = words_with_repetitions if repeated else words_without_repetitions
            clue_position = 5 if repeated else 3
            matching = [words for order in itertools.permutations(LETTERS) if (words := word_lists(order))[clue_position - 1] == clue]
            if expected_position is None:
                self.assertEqual(len(matching), 1, f"seed {seed}: {text}")
                words = matching[0]
                query = printed[1]
                expected = words[words.index(query) + (1 if "после" in text else -1)]
            else:
                expected = {words[expected_position - 1] for words in matching}
            if isinstance(expected, set):
                self.assertIn(generated["answer"], expected, f"seed {seed}: {text}")
            else:
                self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            self.assertNotIn("{", text, f"seed {seed}")

    def test_next_word(self) -> None:
        self.check("alphabet_permutation_next", repeated=False, expected_position=None)

    def test_previous_word(self) -> None:
        self.check("alphabet_permutation_previous", repeated=False, expected_position=None)

    def test_first_word(self) -> None:
        self.check("alphabet_permutation_first", repeated=False, expected_position=1)

    def test_last_repeated_word(self) -> None:
        self.check("alphabet_repetition_last", repeated=True, expected_position=256)


if __name__ == "__main__":
    unittest.main()
