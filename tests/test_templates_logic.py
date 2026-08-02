"""Независимая проверка логических задач с показаниями свидетелей.

Решатель теста разбирает готовое условие: вытаскивает имена говорящих
и то, на кого каждый указывает, а затем примеряет вину на каждого
по очереди. Имена берутся из текста, а не из параметров шаблона, —
так проверяется заодно, что высказывания напечатаны про тех, про кого надо.

Отдельно закреплена корректность: виновный обязан быть единственным.
Показания могут сложиться так, что подходят двое или ни одного, и тогда
у задачи нет ответа, а ключ печатается один.
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


class ThreeWitnessesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_witnesses_one_truth"]

    def read(self, text: str) -> tuple[list[str], list[str]]:
        """Кто говорил и на кого указал — прямо из напечатанного условия."""
        said = re.findall(r"([^.«»]+?) сказал[а]?: «Это ([^»]+)»", text)
        # Имя в начале фразы пишется с заглавной, внутри — со строчной:
        # «Старуха Шапокляк сказала: „Это старуха Шапокляк“». Сравнивать
        # их можно только в одном регистре.
        speakers = [speaker.strip().lower() for speaker, _ in said]
        claims = [target.strip().lower() for _, target in said]
        return speakers, claims

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            speakers, claims = self.read(text)
            self.assertEqual(len(speakers), 3, f"seed {seed}: {text}")

            # Решение с нуля: примеряем вину на каждого и считаем, сколько
            # высказываний при этом истинны.
            fits = [
                suspect for suspect in speakers
                if sum(1 for claim in claims if claim == suspect) == 1
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            self.assertEqual(generated["answer_text"].lower(), fits[0], f"seed {seed}: {text}")

    def test_nobody_speaks_about_himself(self) -> None:
        """«Пьеро сказал: „Это Пьеро“» — так по-русски не говорят."""
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            speakers, claims = self.read(text)
            for speaker, claim in zip(speakers, claims):
                self.assertNotEqual(speaker, claim, f"seed {seed}: {text}")

    def test_all_three_are_different_people(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            speakers, _claims = self.read(text)
            self.assertEqual(len(set(speakers)), 3, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику: показания «Алёша», «Добрыня», «я» → Добрыня."""
        claims = [2, 0, 2]        # третий указывает на себя
        fits = [suspect for suspect in range(3)
                if sum(1 for claim in claims if claim == suspect) == 1]
        self.assertEqual(fits, [0], "в задаче 752 виноват Добрыня")


class CircleOfLiarsTests(unittest.TestCase):
    """Перебор расстановок правдивцев и лжецов по кругу."""

    TEMPLATE = LIBRARY["circle_of_liars"]

    def solve(self, people: int, text: str) -> set[int]:
        """Все возможные числа правдивцев при высказывании из условия."""
        from itertools import product

        if "Все остальные" in text:
            claim = lambda seats, i: all(  # noqa: E731
                not seats[j] for j in range(people) if j != i)
        elif "Один мой сосед" in text:
            claim = lambda seats, i: (  # noqa: E731
                seats[(i - 1) % people] != seats[(i + 1) % people])
        else:
            span = {"Двое": 2, "Трое": 3, "Четверо": 4}[text.split("«")[1].split()[0]]
            claim = lambda seats, i: all(  # noqa: E731
                not seats[(i + step) % people] for step in range(1, span + 1))

        return {
            sum(seats) for seats in product([True, False], repeat=people)
            if all(seats[i] == claim(seats, i) for i in range(people))
        }

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            people = int(re.search(r"сидят (\d+)", text).group(1))
            counts = self.solve(people, text)

            self.assertEqual(len(counts), 1, f"seed {seed}: подходят {counts} — {text}")
            truthful = counts.pop()
            expected = truthful if "правдивцев" in text else people - truthful
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_source_examples_reproduce(self) -> None:
        """Контроль: 10 сидящих и «следующие 4 лжецы» дают 8 лжецов."""
        text = "«Четверо следующих за мной по часовой стрелке — лжецы»"
        self.assertEqual(self.solve(10, text), {2})
        neighbours = "«Один мой сосед лжец, а другой правдивец»"
        self.assertEqual(self.solve(7, neighbours), {0}, "при семи лгут все")

    def test_both_questions_occur(self) -> None:
        seen = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add("правдивцев" in text)
        self.assertEqual(seen, {True, False}, "выпадает только один вопрос")


if __name__ == "__main__":
    unittest.main()
