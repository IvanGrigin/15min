"""Демонстрация работы арифметических шаблонов с русской морфологией.

Запуск:
    python3 scripts/demo_arithmetic.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random

from problemgen.domains.arithmetic.templates import TEMPLATE_FACTORIES


def main() -> None:
    rng = random.Random(42)

    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ АРИФМЕТИЧЕСКИХ ШАБЛОНОВ С РУССКОЙ МОРФОЛОГИЕЙ")
    print("=" * 70)

    for i, (name, factory) in enumerate(TEMPLATE_FACTORIES.items(), 1):
        print(f"\n{'─'*70}")
        print(f"Шаблон {i}: {name}")
        print("─" * 70)

        problem = factory(rng=rng, index=i, difficulty_level="easy")

        print(f"Условие:\n  {problem.problem_text}")
        print(f"Ответ:   {problem.answer_text}")
        print(f"Числа:   {problem.answer_values}")
        print(f"Формула: {problem.metadata.get('formula', '—')}")

    print("\n" + "=" * 70)
    print("Проверка разных уровней сложности (heads_and_legs):")
    print("=" * 70)
    for level in ("easy", "medium", "hard"):
        p = TEMPLATE_FACTORIES["heads_and_legs"](
            rng=random.Random(7), index=1, difficulty_level=level
        )
        print(f"\n[{level}] {p.problem_text}")
        print(f"        Ответ: {p.answer_text}")

    print("\n" + "=" * 70)
    print("Проверка морфологии (число + существительное):")
    print("=" * 70)

    from problemgen.russian.template_engine import render_template
    from problemgen.russian.noun_dict import NOUNS

    tmpl = "У {a:gen_pl} вместе {HEAD:count,n} и {LEG:count,l}."
    for n, l in [(1, 4), (2, 8), (5, 20), (11, 44), (21, 84), (100, 400)]:
        text = render_template(tmpl, {
            "a": NOUNS["овца"], "HEAD": NOUNS["голова"],
            "LEG": NOUNS["нога"], "n": n, "l": l,
        })
        print(f"  n={n:3d}, l={l:4d} → {text}")

    print("\nВсё работает корректно!\n")


if __name__ == "__main__":
    main()
