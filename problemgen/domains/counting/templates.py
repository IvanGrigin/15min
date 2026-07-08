from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from problemgen.core.models import ProblemRecord, TemplateDescriptor
from problemgen.core.story_worlds import StoryContext
from problemgen.core.themes import ThemeConfig
from problemgen.russian import count_with_word_ru, normalize_sentence


@dataclass(frozen=True)
class NumberRange:
    min_value: int
    max_value: int

    def sample(self, rng: random.Random) -> int:
        return rng.randint(self.min_value, self.max_value)


COUNTING_RANGES: Dict[str, Dict[str, NumberRange]] = {
    "easy": {
        "small": NumberRange(2, 12),
        "large": NumberRange(4, 18),
    },
    "medium": {
        "small": NumberRange(15, 60),
        "large": NumberRange(20, 90),
    },
    "hard": {
        "small": NumberRange(90, 350),
        "large": NumberRange(120, 450),
    },
}


def list_templates() -> List[TemplateDescriptor]:
    return [
        TemplateDescriptor(
            code="count_total_groups",
            label="Сумма двух групп",
            description="Нужно сложить количество объектов в двух группах одного сюжета.",
        ),
        TemplateDescriptor(
            code="count_missing_group",
            label="Неизвестная часть",
            description="По общему количеству и одной известной части найти вторую часть.",
        ),
    ]


def generate_total_groups(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    theme: ThemeConfig,
    story_context: StoryContext | None = None,
) -> ProblemRecord:
    first = COUNTING_RANGES[difficulty_level]["small"].sample(rng)
    second = COUNTING_RANGES[difficulty_level]["large"].sample(rng)
    total = first + second
    hero = story_context.lead_character if story_context else rng.choice(theme.heroes)
    item_forms = theme.count_item
    location = story_context.location if story_context else theme.location
    story_payload = {
        "theme_code": theme.code,
        "theme_label": theme.label,
        "location": location,
        "unit_short": "",
        "hero": hero,
    }
    if story_context:
        story_payload.update(story_context.to_metadata())

    problem_text = normalize_sentence(
        f"В мире «{story_context.world_title}» {hero} видит {count_with_word_ru(first, item_forms)} у первой метки "
        f"и {count_with_word_ru(second, item_forms)} у второй метки. "
        f"Сколько {item_forms.many} всего видит {hero}?"
        if story_context
        else
        f"{theme.location.capitalize()} {hero} видит {count_with_word_ru(first, item_forms)} у первой метки "
        f"и {count_with_word_ru(second, item_forms)} у второй метки. "
        f"Сколько {item_forms.many} всего видит {hero}?"
    )

    return ProblemRecord(
        code=f"CNT-TOT-{index:05d}",
        category="counting",
        domain="counting",
        template_name="count_total_groups",
        problem_text=problem_text,
        answer_text=count_with_word_ru(total, item_forms),
        answer_values=[total],
        difficulty={
            "level": difficulty_level,
            "first_value_digits": len(str(first)),
            "second_value_digits": len(str(second)),
            "answer_digits": len(str(total)),
        },
        story=story_payload,
        metadata={
            "topic": "счет",
            "subtype": "сумма двух групп",
            "formula": "a + b",
        },
        variables={"first_group": first, "second_group": second},
        intermediate_values={"sum": total},
        relations=["Складываются количества двух групп одного типа объектов."],
    )


def generate_missing_group(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    theme: ThemeConfig,
    story_context: StoryContext | None = None,
) -> ProblemRecord:
    known = COUNTING_RANGES[difficulty_level]["small"].sample(rng)
    missing = COUNTING_RANGES[difficulty_level]["small"].sample(rng)
    total = known + missing
    hero = story_context.lead_character if story_context else rng.choice(theme.heroes)
    item_forms = theme.count_item
    location = story_context.location if story_context else theme.location
    story_payload = {
        "theme_code": theme.code,
        "theme_label": theme.label,
        "location": location,
        "unit_short": "",
        "hero": hero,
    }
    if story_context:
        story_payload.update(story_context.to_metadata())

    problem_text = normalize_sentence(
        f"В мире «{story_context.world_title}» {hero} знает, что всего там {count_with_word_ru(total, item_forms)}. "
        f"У первой метки находится {count_with_word_ru(known, item_forms)}. "
        f"Сколько {item_forms.many} находится у второй метки?"
        if story_context
        else
        f"{theme.location.capitalize()} {hero} знает, что всего там {count_with_word_ru(total, item_forms)}. "
        f"У первой метки находится {count_with_word_ru(known, item_forms)}. "
        f"Сколько {item_forms.many} находится у второй метки?"
    )

    return ProblemRecord(
        code=f"CNT-MIS-{index:05d}",
        category="counting",
        domain="counting",
        template_name="count_missing_group",
        problem_text=problem_text,
        answer_text=count_with_word_ru(missing, item_forms),
        answer_values=[missing],
        difficulty={
            "level": difficulty_level,
            "known_digits": len(str(known)),
            "total_digits": len(str(total)),
            "answer_digits": len(str(missing)),
        },
        story=story_payload,
        metadata={
            "topic": "счет",
            "subtype": "неизвестная часть",
            "formula": "total - known",
        },
        variables={"known_group": known, "total_group": total},
        intermediate_values={"missing_group": missing},
        relations=["Искомая часть находится вычитанием известной части из общего количества."],
    )
