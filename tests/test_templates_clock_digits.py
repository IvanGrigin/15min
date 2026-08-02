"""Независимая проверка поиска момента на табло по свойству цифр.

Решатель теста читает условие как человек: стартовое время, номер совпадения
словом («в седьмой раз») и само свойство («все цифры будут различными»).
Затем идёт по секундам вперёд и считает совпадения сам, не заглядывая
ни в параметры шаблона, ни в его решатель.

Так проверяется и арифметика, и то, что слова описывают ровно ту проверку,
которую делает движок: если «все различны» подменить на «четыре одинаковых»
при неизменном тексте, тест упадёт.
"""
from __future__ import annotations

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
SEEDS = range(40)
DAY = 24 * 60 * 60

ORDINALS = {
    "впервые": 1, "во второй раз": 2, "в третий раз": 3, "в четвёртый раз": 4,
    "в пятый раз": 5, "в шестой раз": 6, "в седьмой раз": 7, "в восьмой раз": 8,
    "в девятый раз": 9, "в десятый раз": 10, "в одиннадцатый раз": 11,
    "в двенадцатый раз": 12,
}


def digits_at(seconds: int) -> str:
    seconds %= DAY
    return f"{seconds // 3600:02d}{seconds % 3600 // 60:02d}{seconds % 60:02d}"


class ClockDigitsSearchTests(unittest.TestCase):
    TEMPLATE = LIBRARY["clock_digits_search"]

    def read(self, text: str) -> tuple[int, int, str]:
        """Разобрать условие: старт, номер совпадения и свойство цифр."""
        hours, minutes, seconds = (
            int(value) for value in re.search(r"(\d{2}):(\d{2}):(\d{2})", text).groups())
        start = hours * 3600 + minutes * 60 + seconds
        phrase = next(word for word in ORDINALS if word in text)
        rule = "different" if "различными" in text else "four_same"
        return start, ORDINALS[phrase], rule

    def solve(self, start: int, occurrence: int, rule: str) -> int:
        """Идти по секундам вперёд и считать совпадения свойства."""
        seen = 0
        for offset in range(1, DAY + 1):
            moment = (start + offset) % DAY
            text = digits_at(moment)
            if rule == "different":
                ok = len(set(text)) == 6
            else:
                ok = any(text.count(digit) == 4 for digit in set(text))
            if ok:
                seen += 1
                if seen == occurrence:
                    return moment
        raise AssertionError("свойство не встретилось за сутки")

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            start, occurrence, rule = self.read(text)
            moment = self.solve(start, occurrence, rule)

            if "Через сколько секунд" in text:
                expected = (moment - start) % DAY
            else:
                expected = moment
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_start_moment_itself_does_not_count(self) -> None:
        """Вопрос всегда «после этого», значит отсчёт со следующей секунды."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            start, _occurrence, _rule = self.read(generated["rendered_problem"])
            answer = generated["answer"]
            moment = answer if answer >= 3600 else (start + answer) % DAY
            self.assertNotEqual(moment, start, f"seed {seed}: ответ совпал со стартом")

    def test_both_questions_and_both_rules_occur(self) -> None:
        """Один вопрос на шаблон — мало; здесь их два, и свойства тоже два."""
        questions, rules = set(), set()
        for seed in range(80):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            questions.add("Через сколько секунд" in text)
            rules.add("различными" in text)
        self.assertEqual(questions, {True, False}, "выпадает только один вопрос")
        self.assertEqual(rules, {True, False}, "выпадает только одно свойство")

    def test_answer_stays_within_the_hour(self) -> None:
        """Иначе задача становится про переход через полночь, а не про цифры."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            start, _occurrence, _rule = self.read(generated["rendered_problem"])
            answer = generated["answer"]
            gap = answer if answer < 3600 else (answer - start) % DAY
            self.assertLessEqual(gap, 3000, f"seed {seed}: разрыв {gap} секунд")

    def test_text_is_clean(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text, f"seed {seed}")
            self.assertNotIn("  ", text, f"seed {seed}")
            self.assertNotIn("в 1-й раз", text, f"seed {seed}: не по-русски")
            self.assertTrue(text[0].isupper(), f"seed {seed}")
            self.assertEqual(text.rstrip()[-1], "?", f"seed {seed}")


if __name__ == "__main__":
    unittest.main()
