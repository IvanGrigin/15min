"""Независимая проверка темы «Алфавитный порядок».

Решатель ничего не знает ни о параметрах шаблона, ни о разыгранном алфавите.
Он читает напечатанное условие — буквы языка, сколько слов выписано, на каком
месте стоит слово-подсказка и о чём спрашивают — и решает задачу так, как её
решает ребёнок: перебирает все порядки букв, оставляет согласованные
с подсказкой и смотрит, что получается в ответе.

Отсюда три вещи, которые здесь проверяются и которые формула шаблона проверить
не может:

* ответ верен по тексту, а не по внутренним значениям;
* там, где ответ обязан быть единственным, подсказка действительно сужает круг
  алфавитов до одного;
* там, где верных ответов несколько, в ключ попали все — иначе ребёнок,
  назвавший второй, прав, а получит крестик.

Отдельно проверяется разнообразие. До перевода темы на разыгрываемый алфавит
все пять шаблонов давали ровно по два условия каждый: параметр `case ∈ {1, 2}`
и все слова строками в `derived_values`. Тест на число различных условий стоит
затем, чтобы такой откат было видно сразу.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from itertools import permutations, product
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(30)


def read_condition(text: str) -> dict[str, object]:
    """Разобрать напечатанное условие так, как его читает решающий."""
    letters_match = re.search(r"язык из букв ([^.]+)\.", text)
    assert letters_match, text
    letters = tuple(part.strip() for part in letters_match.group(1).split(","))

    # Счётный слот ставит между числом и словом неразрывный пробел.
    total = int(re.search(r"[Вв]се (\d+)[\s\u00a0]+слов", text).group(1))
    repetitions = "с повторениями" in text
    length = 4 if repetitions else len(letters)

    clue_match = re.search(r"(\d+)-м словом (?:будет|стало) ([А-ЯЁ]+)", text)
    assert clue_match, text
    return {
        "letters": letters,
        "total": total,
        "length": length,
        "repetitions": repetitions,
        "clue_position": int(clue_match.group(1)),
        "clue_word": clue_match.group(2),
    }


def orderings(condition: dict[str, object]) -> list[list[str]]:
    """Все списки слов, согласованные с подсказкой из условия."""
    letters = condition["letters"]
    raw = (
        product(letters, repeat=condition["length"]) if condition["repetitions"]
        else permutations(letters)
    )
    words = ["".join(item) for item in raw]
    matching = []
    for order in permutations(letters):
        rank = {letter: index for index, letter in enumerate(order)}
        listed = sorted(words, key=lambda word: [rank[letter] for letter in word])
        if listed[condition["clue_position"] - 1] == condition["clue_word"]:
            matching.append(listed)
    return matching


def possible_answers(text: str) -> set[str]:
    """Все ответы, возможные при алфавитах, согласованных с условием."""
    condition = read_condition(text)
    found = set()
    for listed in orderings(condition):
        assert len(listed) == condition["total"], "число слов в условии не сходится"
        if "будет первым" in text:
            found.add(listed[0])
        elif "может быть последним" in text:
            found.add(listed[-1])
        elif "будет" in text and re.search(r"будет (\d+)-м", text):
            position = int(re.search(r"будет (\d+)-м", text).group(1))
            found.add(listed[position - 1])
        else:
            # «после слова МАРО?» и «перед словом МОАР?» — падеж разный.
            query = re.search(r"слов[аом]+[\s\u00a0]+([А-ЯЁ]+)\?", text).group(1)
            index = listed.index(query)
            found.add(listed[index + 1] if "после" in text else listed[index - 1])
    return found


class AlphabetOrderTests(unittest.TestCase):
    """Ответ каждого шаблона сверяется с перебором по напечатанному тексту."""

    UNIQUE = (
        "alphabet_permutation_first",
        "alphabet_permutation_position",
        "alphabet_permutation_next",
        "alphabet_permutation_previous",
    )

    def test_single_answer_templates_are_unambiguous_and_correct(self) -> None:
        for template_id in self.UNIQUE:
            for seed in SEEDS:
                generated = generate_active_template(LIBRARY[template_id], random.Random(seed))
                text = generated["rendered_problem"]
                found = possible_answers(text)
                self.assertEqual(
                    len(found), 1,
                    f"{template_id}, seed {seed}: подсказка допускает {len(found)} ответов "
                    f"({', '.join(sorted(found))}), а ключ печатает один — {text}",
                )
                self.assertEqual(
                    generated["answer"], found.pop(),
                    f"{template_id}, seed {seed}: {text}",
                )

    def test_repetition_key_lists_every_correct_answer(self) -> None:
        """Здесь верных ответов заведомо несколько, и все обязаны быть в ключе.

        Ровно этого не хватало прежней версии: подсказка на пятом месте всегда
        оставляет два возможных последних слова, а печаталось одно.
        """
        seen_ambiguous = False
        for seed in SEEDS:
            generated = generate_active_template(
                LIBRARY["alphabet_repetition_last"], random.Random(seed))
            text = generated["rendered_problem"]
            found = possible_answers(text)
            printed = set(generated["answer"])
            self.assertEqual(printed, found, f"seed {seed}: {text}")
            answer_text = generated["answer_text"]
            for word in found:
                self.assertIn(word, answer_text, f"seed {seed}: ключ не называет {word}")
            if len(found) > 1:
                seen_ambiguous = True
                self.assertIn(" или ", answer_text, f"seed {seed}: варианты слиты в один ответ")
        self.assertTrue(seen_ambiguous, "ни разу не встретилась неоднозначность — проверять нечего")

    def test_condition_states_the_true_number_of_words(self) -> None:
        """«Все 24 слова» для четырёх букв, «все 120» для пяти — не наоборот."""
        for template_id in (*self.UNIQUE, "alphabet_repetition_last"):
            for seed in SEEDS:
                text = generate_active_template(
                    LIBRARY[template_id], random.Random(seed))["rendered_problem"]
                condition = read_condition(text)
                expected = (
                    len(condition["letters"]) ** condition["length"]
                    if condition["repetitions"]
                    else len(list(permutations(condition["letters"])))
                )
                self.assertEqual(
                    condition["total"], expected,
                    f"{template_id}, seed {seed}: в условии {condition['total']} слов, "
                    f"а из букв получается {expected} — {text}",
                )

    def test_templates_are_not_a_handful_of_frozen_cases(self) -> None:
        """Защита от возврата к «двум случаям на шаблон».

        Порог намеренно грубый: он ловит вырождение темы, а не колеблется
        от смены набора языков в данных.
        """
        for template_id in (*self.UNIQUE, "alphabet_repetition_last"):
            distinct = {
                generate_active_template(
                    LIBRARY[template_id], random.Random(seed))["rendered_problem"]
                for seed in range(60)
            }
            self.assertGreater(
                len(distinct), 20,
                f"{template_id}: всего {len(distinct)} различных условий на 60 жеребьёвок",
            )

    def test_the_alphabet_itself_never_leaks_into_the_text(self) -> None:
        """Настоящий порядок букв — то, что требуется найти; печатать его нельзя."""
        for template_id in (*self.UNIQUE, "alphabet_repetition_last"):
            for seed in SEEDS:
                generated = generate_active_template(LIBRARY[template_id], random.Random(seed))
                order = "".join(generated["parameters"]["abc"])
                self.assertNotIn(
                    order, generated["rendered_problem"].replace(" ", ""),
                    f"{template_id}, seed {seed}: алфавит виден в условии",
                )


if __name__ == "__main__":
    unittest.main()
