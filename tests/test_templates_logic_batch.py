"""Батч Б6: логика, высказывания и оценки по неравенству.

Решатели перебирают все расстановки правды и лжи, а не повторяют вывод
шаблона. Для парламента это значит: пройти все возможные числа лжецов
и оставить те, при которых сходятся оба вида высказываний. Для тетради —
проверить каждое утверждение на согласованность с самим собой. Для
неравенства с кратностями — подставить множество допустимых весов и
убедиться, что ответ не зависит от выбора.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)
SPACE = "[\\s ]+"


class ParliamentTests(unittest.TestCase):
    TEMPLATE = LIBRARY["parliament_liars_majority"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(rf"лжецов (\d+){SPACE}депутат", text).group(1))

            # Решение с нуля: перебираем число лжецов и проверяем оба вида
            # высказываний. Годится то, при котором сходятся все депутаты.
            fits = []
            for liars in range(total + 1):
                knights = total - liars
                knight_ok = knights == 0 or liars > (total - 1) / 2
                liar_ok = liars == 0 or (liars - 1) <= (total - 1) / 2
                if knight_ok and liar_ok:
                    fits.append(liars)
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            # «рыцарей» есть и в названии острова, поэтому смотрим сам вопрос.
            asks_knights = "Сколько рыцарей" in text
            expected = total - fits[0] if asks_knights else fits[0]
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class NotebookTests(unittest.TestCase):
    TEMPLATE = LIBRARY["notebook_self_counting_statements"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]

            if "Сколько всего утверждений" in text:
                right = int(re.search(r"с номером (\d+)", text).group(1))
                # Верно утверждение с номером n−1, значит всего на один больше.
                self.assertEqual(generated["answer"], right + 1, f"seed {seed}: {text}")
                continue

            total = int(re.search(rf"записаны (\d+){SPACE}утвержден", text).group(1))
            # Решение с нуля: перебираем, сколько утверждений неверно,
            # и проверяем согласованность каждого утверждения с этим числом.
            fits = []
            for wrong in range(total + 1):
                claims = [(number == wrong) for number in range(1, total + 1)]
                if sum(1 for claim in claims if not claim) == wrong:
                    fits.append(wrong)
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")


class TransitiveWeightsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["transitive_weights_with_multiples"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            few, many = values["few"], values["many"]
            ask_light, ask_heavy = values["ask_light"], values["ask_heavy"]
            text = generated["rendered_problem"]

            # Решение с нуля: перебираем допустимые веса. Тяжёлый предмет
            # берём за единицу, лёгкий — чуть больше нижней границы и много
            # выше её. Ответ не должен зависеть от выбора.
            verdicts = set()
            safe_counts = set()
            for extra in (Fraction(1, 100), Fraction(1, 3), Fraction(5), Fraction(50)):
                heavy_one = Fraction(1)
                light_one = Fraction(many, few) * heavy_one + extra
                verdicts.add(ask_light * light_one > ask_heavy * heavy_one)
                safe_counts.add(max(
                    count for count in range(1, 200)
                    if ask_light * light_one > count * heavy_one))
            self.assertEqual(verdicts, {True}, f"seed {seed}: ответ зависит от весов — {text}")

            if "наибольшее число" in text:
                # Гарантировать можно лишь то, что верно при любых весах.
                self.assertLessEqual(generated["answer"], min(safe_counts), f"seed {seed}")
                self.assertGreaterEqual(generated["answer"], ask_heavy, f"seed {seed}")
            else:
                self.assertEqual(generated["answer_text"], "первое", f"seed {seed}: {text}")


class ThreeBoxesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_boxes_wrong_labels"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first, second, third = (values.strip() for values in
                                    re.search(r"лежат (.+?), (.+?) и (.+?) —", text).groups())

            # Решение с нуля: перебираем все шесть расстановок.
            from itertools import permutations
            fits = [
                order for order in permutations((first, second, third))
                if order[0] != first and order[1] != second
                and order[2] not in (first, third)
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: расстановок {len(fits)} — {text}")
            order = fits[0]
            index = 1 if "во второй банке" in text else (2 if "в третьей банке" in text else 0)
            self.assertEqual(generated["answer_text"], order[index], f"seed {seed}: {text}")


class LiarChainTests(unittest.TestCase):
    TEMPLATE = LIBRARY["liar_chain_impossible_claim"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]

            # Решение с нуля: перебираем, кем может быть каждый, и оставляем
            # расстановки, при которых все высказывания согласованы.
            confirms = "говорит чистую правду" in text
            fits = []
            for first_knight in (True, False):
                for third_knight in (True, False):
                    # Пересказ «он назвал себя лжецом» невозможен, значит
                    # первый говорящий лжёт при любом соседе.
                    if first_knight:
                        continue
                    said_truth = first_knight
                    if third_knight != (said_truth if confirms else not said_truth):
                        continue
                    fits.append((first_knight, third_knight))
            self.assertEqual(len(fits), 1, f"seed {seed}: расстановок {len(fits)} — {text}")
            first_knight, third_knight = fits[0]
            asked_first = text.rstrip("?").endswith("рыцарь или лжец") and \
                re.search(r"Кто (.+?) — рыцарь", text).group(1) in text.split("сказал")[0]
            wanted = first_knight if asked_first else third_knight
            self.assertEqual(generated["answer_text"], "рыцарь" if wanted else "лжец",
                             f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
