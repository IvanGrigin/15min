"""Числа, оканчивающиеся на 1, в счётных слотах: согласование соседних слов.

Счётный слот `{noun:count,n}` при числе 1, 21, 81 ставит существительное
в именительный падеж единственного числа — и это верно само по себе.
Ломается не форма слова, а согласование с тем, что стоит рядом, поэтому
`tests/test_numeral_agreement.py` этот класс не видит: там сверяется
«81 рыцарь» с таблицей форм, и оно сходится.

Два случая, оба уже случались в выдаче и оба перечислены в AGENTS §10:

1. **Безличный глагол среднего рода.** «Всего в очереди оказалось 81 рыцарь» —
   при числительном на 1 сказуемое обязано стоять в единственном числе
   мужского рода: «оказался 81 рыцарь». Средний род возможен только при
   числах, не кончающихся на 1 («оказалось 45 волшебников»). Исключений
   у правила нет: сочетание «оказалось/вышло/пришло + N1 + слово» неверно
   всегда, чинится либо сказуемым, либо запретом таких чисел.

2. **Винительный одушевлённого.** «Насчитал 21 рыцарь» — у одушевлённого
   винительный совпадает с родительным: «насчитал 21 рыцаря». Проверяется
   только по словарю: одушевлённое, у которого `acc` не совпадает с `nom`.

Оба класса лечатся ограничением `X % 10 != 1 or X % 100 == 11` на число:
одиннадцать и его сотни ведут себя как множественное («оказалось 111 рыцарей»),
поэтому из-под правила выведены.
"""
from __future__ import annotations

import json
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

SEEDS = range(40)
# Между числом и словом счётный слот ставит неразрывный пробел.
SPACE = "[\\s ]+"

# Безличные формы среднего рода, после которых число на 1 невозможно.
NEUTER_PREDICATES = (
    "оказалось", "вышло", "получилось", "осталось", "пришло", "встало",
    "набралось", "собралось", "стало", "записано", "выписано", "съедено",
    "продано", "куплено", "сделано", "посажено", "роздано",
)
# Переходные глаголы прошедшего времени: после них одушевлённое стоит
# в винительном, а счётный слот при числе на 1 даёт именительный.
TRANSITIVE_PAST = (
    "насчитал", "насчитала", "пересчитал", "пересчитала", "собрал", "собрала",
    "увидел", "увидела", "заметил", "заметила", "позвал", "позвала",
    "поймал", "поймала", "привёл", "привела", "посадил", "посадила",
    "купил", "купила", "нашёл", "нашла",
)


def animate_nominatives() -> dict[str, str]:
    """Именительный → винительный для одушевлённых, где формы различаются."""
    payload = json.loads(
        (PROJECT_ROOT / "data" / "language" / "nouns" / "russian_nouns.json")
        .read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for lemma, entry in payload.items():
        if lemma.startswith("_") or not isinstance(entry, dict):
            continue
        forms = entry.get("forms") or {}
        nom, accusative = forms.get("nom"), forms.get("acc")
        if entry.get("animate") and nom and accusative and nom != accusative:
            result[nom] = accusative
    return result


def ends_in_one(number: int) -> bool:
    """Число требует согласования по единственному числу: 1, 21, 81, но не 11."""
    return number % 10 == 1 and number % 100 != 11


class NumeralEndingInOneTests(unittest.TestCase):
    """Ни одно условие не ставит число на 1 туда, где оно ломает соседа."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.library = load_library()
        cls.animate = animate_nominatives()
        cls.texts: list[tuple[str, int, str]] = []
        for template in cls.library:
            for seed in SEEDS:
                try:
                    generated = generate_active_template(template, random.Random(seed))
                except Exception:  # noqa: BLE001 — генерацию проверяют другие тесты
                    continue
                cls.texts.append((template["template_id"], seed, generated["rendered_problem"]))

    def test_texts_were_generated(self) -> None:
        self.assertGreater(len(self.texts), 1000, "выдача не собралась, проверять нечего")

    def test_no_neuter_predicate_before_number_ending_in_one(self) -> None:
        pattern = re.compile(
            r"\b(" + "|".join(NEUTER_PREDICATES) + r")" + SPACE + r"(\d+)" + SPACE + r"([а-яё]+)",
            re.IGNORECASE)
        offenders = []
        for template_id, seed, text in self.texts:
            for verb, raw_number, word in pattern.findall(text):
                if ends_in_one(int(raw_number)):
                    offenders.append(
                        f"{template_id} (seed {seed}): «{verb} {raw_number} {word}» — "
                        f"при числе на 1 сказуемое в единственном числе")
        self.assertEqual(sorted(set(offenders))[:8], [],
                         f"всего нарушений: {len(set(offenders))}")

    def test_animate_after_transitive_verb_is_accusative(self) -> None:
        pattern = re.compile(
            r"\b(" + "|".join(TRANSITIVE_PAST) + r")" + SPACE
            + r"(?:[а-яё]+" + SPACE + r"){0,3}?(\d+)" + SPACE + r"([а-яё]+)",
            re.IGNORECASE)
        offenders = []
        for template_id, seed, text in self.texts:
            for verb, raw_number, word in pattern.findall(text):
                if not ends_in_one(int(raw_number)):
                    continue
                accusative = self.animate.get(word.lower())
                if accusative:
                    offenders.append(
                        f"{template_id} (seed {seed}): «{verb} {raw_number} {word}», "
                        f"нужно «{raw_number} {accusative}»")
        self.assertEqual(sorted(set(offenders))[:8], [],
                         f"всего нарушений: {len(set(offenders))}")


if __name__ == "__main__":
    unittest.main()
