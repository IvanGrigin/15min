from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from problemgen.core.models import ProblemRecord, TemplateDescriptor
from problemgen.core.themes import ThemeConfig
from problemgen.russian import NounForms, count_with_word_ru, normalize_sentence


@dataclass(frozen=True)
class NumberRange:
    min_value: int
    max_value: int

    def sample(self, rng: random.Random) -> int:
        return rng.randint(self.min_value, self.max_value)


COMBINATORICS_RANGES: Dict[str, NumberRange] = {
    "easy": NumberRange(2, 5),
    "medium": NumberRange(4, 9),
    "hard": NumberRange(7, 15),
}

COMBINATION_FORMS = NounForms("комбинация", "комбинации", "комбинаций")
ROUTE_FORMS = NounForms("маршрут", "маршрута", "маршрутов")
OPTION_FORMS = NounForms("вариант", "варианта", "вариантов")


def list_templates() -> List[TemplateDescriptor]:
    return [
        TemplateDescriptor(
            code="combo_outfit_pairs",
            label="Комбинации двух групп",
            description="Правило произведения для выбора по одному варианту из двух независимых групп.",
        ),
        TemplateDescriptor(
            code="combo_route_pairs",
            label="Комбинации маршрутов",
            description="Правило произведения для выбора двух последовательных этапов пути.",
        ),
    ]


def generate_outfit_pairs(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    theme: ThemeConfig,
) -> ProblemRecord:
    first = COMBINATORICS_RANGES[difficulty_level].sample(rng)
    second = COMBINATORICS_RANGES[difficulty_level].sample(rng)
    total = first * second
    hero = rng.choice(theme.heroes)

    problem_text = normalize_sentence(
        f"{theme.location.capitalize()} {hero} может выбрать {count_with_word_ru(first, theme.choice_a)} "
        f"и {count_with_word_ru(second, theme.choice_b)}. "
        f"Сколько разных комбинаций можно составить, если взять по одному варианту из каждой группы?"
    )

    return ProblemRecord(
        code=f"COM-OUT-{index:05d}",
        category="combinatorics",
        domain="combinatorics",
        template_name="combo_outfit_pairs",
        problem_text=problem_text,
        answer_text=count_with_word_ru(total, COMBINATION_FORMS),
        answer_values=[total],
        difficulty={
            "level": difficulty_level,
            "choice_a_digits": len(str(first)),
            "choice_b_digits": len(str(second)),
            "answer_digits": len(str(total)),
        },
        story={
            "theme_code": theme.code,
            "theme_label": theme.label,
            "location": theme.location,
            "unit_short": "",
            "hero": hero,
        },
        metadata={
            "topic": "комбинаторика",
            "subtype": "правило произведения",
            "formula": "a * b",
        },
        variables={"choices_a": first, "choices_b": second},
        intermediate_values={"product": total},
        relations=["Количество комбинаций равно произведению числа независимых выборов."],
    )


def generate_route_pairs(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    theme: ThemeConfig,
) -> ProblemRecord:
    first = COMBINATORICS_RANGES[difficulty_level].sample(rng)
    second = COMBINATORICS_RANGES[difficulty_level].sample(rng)
    total = first * second
    hero = rng.choice(theme.heroes)

    problem_text = normalize_sentence(
        f"{theme.location.capitalize()} {hero} может выбрать {count_with_word_ru(first, OPTION_FORMS)} для первого этапа пути "
        f"и {count_with_word_ru(second, OPTION_FORMS)} для второго этапа. "
        f"Сколько разных маршрутов получится?"
    )

    return ProblemRecord(
        code=f"COM-ROU-{index:05d}",
        category="combinatorics",
        domain="combinatorics",
        template_name="combo_route_pairs",
        problem_text=problem_text,
        answer_text=count_with_word_ru(total, ROUTE_FORMS),
        answer_values=[total],
        difficulty={
            "level": difficulty_level,
            "route_a_digits": len(str(first)),
            "route_b_digits": len(str(second)),
            "answer_digits": len(str(total)),
        },
        story={
            "theme_code": theme.code,
            "theme_label": theme.label,
            "location": theme.location,
            "unit_short": "",
            "hero": hero,
        },
        metadata={
            "topic": "комбинаторика",
            "subtype": "маршруты",
            "formula": "a * b",
        },
        variables={"first_stage": first, "second_stage": second},
        intermediate_values={"route_count": total},
        relations=["Каждый выбор первого этапа можно сочетать с каждым выбором второго этапа."],
    )
