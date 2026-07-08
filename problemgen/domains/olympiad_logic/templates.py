from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List

from problemgen.core.models import ProblemRecord, TemplateDescriptor
from problemgen.core.story_worlds import StoryContext, sample_story_context
from problemgen.russian import count_with_word_ru, normalize_sentence

from .solvers import run_digit_erasing_process, solve_birds_count, solve_digit_erasing, solve_shared_payment_debt
from .validators import (
    validate_birds_count,
    validate_digit_erasing,
    validate_shared_payment_debt,
    validate_three_numbers_same_suffix,
)


@dataclass(frozen=True)
class NumberRange:
    min_value: int
    max_value: int

    def sample(self, rng: random.Random) -> int:
        return rng.randint(self.min_value, self.max_value)


OLYMPIAD_RANGES: Dict[str, Dict[str, NumberRange]] = {
    "easy": {
        "digit_start": NumberRange(10, 80),
        "birds_base": NumberRange(4, 20),
        "suffix": NumberRange(0, 25),
        "payment_total": NumberRange(200, 2_000),
        "payment_loan": NumberRange(300, 4_000),
    },
    "medium": {
        "digit_start": NumberRange(40, 250),
        "birds_base": NumberRange(24, 80),
        "suffix": NumberRange(10, 60),
        "payment_total": NumberRange(2_000, 20_000),
        "payment_loan": NumberRange(3_000, 25_000),
    },
    "hard": {
        "digit_start": NumberRange(120, 900),
        "birds_base": NumberRange(84, 240),
        "suffix": NumberRange(30, 95),
        "payment_total": NumberRange(20_000, 120_000),
        "payment_loan": NumberRange(25_000, 160_000),
    },
}


def list_templates() -> List[TemplateDescriptor]:
    return [
        TemplateDescriptor(
            code="digit_erasing",
            label="Зачёркивание последней цифры",
            description="После умножений и зачёркивания последних цифр нужно восстановить исходное число.",
        ),
        TemplateDescriptor(
            code="birds_count",
            label="Ещё столько же, половина и четверть",
            description="По условию о добавлении целой, половины и четверти группы найти исходное количество.",
        ),
        TemplateDescriptor(
            code="three_numbers_same_suffix",
            label="Три трёхзначных числа",
            description="Найти три трёхзначных числа с общей суммой и одинаковыми двумя последними цифрами.",
        ),
        TemplateDescriptor(
            code="shared_payment_debt",
            label="Совместная оплата и долг",
            description="После займа и неравных платежей нужно определить итоговый расчёт между двумя персонажами.",
        ),
    ]


def _story_payload(story_context: StoryContext) -> dict[str, object]:
    return story_context.to_metadata()


def _ensure_story_context(story_context: StoryContext | None, rng: random.Random) -> StoryContext:
    return story_context or sample_story_context(rng=rng)


def generate_digit_erasing(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    story_context: StoryContext | None = None,
) -> ProblemRecord:
    story = _ensure_story_context(story_context, rng)
    lead = story.lead_character
    location = story.location
    multipliers = [(13, 7), (17, 4), (19, 6), (23, 3), (27, 4)]
    phrasing = rng.choice(
        [
            "задумал целое число, умножил его на {m1}, зачеркнул последнюю цифру результата, "
            "полученное число умножил на {m2}, снова зачеркнул последнюю цифру и получил число {final}",
            "взял целое число, умножил его на {m1}, потом стёр последнюю цифру, "
            "полученный результат умножил на {m2}, ещё раз стёр последнюю цифру и получил число {final}",
        ]
    )

    while True:
        start_value = OLYMPIAD_RANGES[difficulty_level]["digit_start"].sample(rng)
        first_multiplier, second_multiplier = rng.choice(multipliers)
        final_value = run_digit_erasing_process(start_value, first_multiplier, second_multiplier)
        if final_value <= 0:
            continue
        solutions = solve_digit_erasing(
            first_multiplier=first_multiplier,
            second_multiplier=second_multiplier,
            final_value=final_value,
        )
        if solutions == [start_value] and validate_digit_erasing(
            start_value=start_value,
            first_multiplier=first_multiplier,
            second_multiplier=second_multiplier,
            final_value=final_value,
        ):
            break

    problem_text = normalize_sentence(
        f"В мире «{story.world_title}» {lead} {phrasing.format(m1=first_multiplier, m2=second_multiplier, final=final_value)}. "
        f"Какое число задумал {lead}?"
    )

    return ProblemRecord(
        code=f"OLY-DIG-{index:05d}",
        category="olympiad_logic",
        domain="olympiad_logic",
        template_name="digit_erasing",
        problem_text=problem_text,
        answer_text=str(start_value),
        answer_values=[start_value],
        difficulty={
            "level": difficulty_level,
            "start_digits": len(str(start_value)),
            "final_digits": len(str(final_value)),
        },
        story=_story_payload(story),
        metadata={
            "topic": "олимпиадная логика",
            "subtype": "зачеркивание последней цифры",
            "formula": "floor(m2 * floor(m1 * x / 10) / 10)",
        },
        variables={
            "first_multiplier": first_multiplier,
            "second_multiplier": second_multiplier,
            "final_value": final_value,
        },
        intermediate_values={},
        relations=["После каждого зачёркивания последней цифры используется целочисленное деление на 10."],
    )


def generate_birds_count(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    story_context: StoryContext | None = None,
) -> ProblemRecord:
    story = _ensure_story_context(story_context, rng)
    lead = story.lead_character
    group_name = rng.choice(["группа друзей", "компания героев", "отряд персонажей"])
    initial_count = OLYMPIAD_RANGES[difficulty_level]["birds_base"].sample(rng) * 4
    total_after_expansion = initial_count + initial_count + initial_count // 2 + initial_count // 4 + 1

    problem_text = normalize_sentence(
        f"В мире «{story.world_title}» {lead} встретил {group_name}. "
        f"«Здравствуйте, {total_after_expansion} персонажей», — сказал {lead}. "
        f"В ответ ему сказали: «Нас не {total_after_expansion}! Если к нам прибавить ещё столько же, "
        f"ещё половину нас, ещё четверть нас и тебя, то всего станет {total_after_expansion}». "
        f"Сколько персонажей было в группе сначала?"
    )

    assert validate_birds_count(initial_count=initial_count, total_after_expansion=total_after_expansion)
    solved = solve_birds_count(total_after_expansion)

    return ProblemRecord(
        code=f"OLY-BRD-{index:05d}",
        category="olympiad_logic",
        domain="olympiad_logic",
        template_name="birds_count",
        problem_text=problem_text,
        answer_text=str(solved),
        answer_values=[solved],
        difficulty={
            "level": difficulty_level,
            "answer_digits": len(str(solved)),
            "target_digits": len(str(total_after_expansion)),
        },
        story=_story_payload(story),
        metadata={
            "topic": "олимпиадная логика",
            "subtype": "столько же, половина и четверть",
            "formula": "x + x + x/2 + x/4 + 1 = total",
        },
        variables={
            "total_after_expansion": total_after_expansion,
        },
        intermediate_values={
            "initial_count": solved,
        },
        relations=["Начальное количество восстанавливается из линейного уравнения с целочисленным ответом."],
    )


def generate_three_numbers_same_suffix(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    story_context: StoryContext | None = None,
) -> ProblemRecord:
    story = _ensure_story_context(story_context, rng)
    lead = story.lead_character

    while True:
        suffix = OLYMPIAD_RANGES[difficulty_level]["suffix"].sample(rng)
        first_digits = sorted(rng.sample(range(1, 10), 3))
        numbers = [digit * 100 + suffix for digit in first_digits]
        target_sum = sum(numbers)
        if validate_three_numbers_same_suffix(numbers=numbers, target_sum=target_sum):
            break

    number_list = ", ".join(str(number) for number in numbers)
    problem_text = normalize_sentence(
        f"В мире «{story.world_title}» {lead} записал три различных трёхзначных числа. "
        f"Их сумма равна {target_sum}. Эти числа отличаются друг от друга только первой цифрой. "
        f"Какие числа мог записать {lead}?"
    )

    return ProblemRecord(
        code=f"OLY-THR-{index:05d}",
        category="olympiad_logic",
        domain="olympiad_logic",
        template_name="three_numbers_same_suffix",
        problem_text=problem_text,
        answer_text=number_list,
        answer_values=numbers,
        difficulty={
            "level": difficulty_level,
            "sum_digits": len(str(target_sum)),
        },
        story=_story_payload(story),
        metadata={
            "topic": "олимпиадная логика",
            "subtype": "три числа с общим суффиксом",
            "formula": "100*a + s, 100*b + s, 100*c + s",
        },
        variables={
            "target_sum": target_sum,
            "suffix": suffix,
        },
        intermediate_values={
            "numbers": numbers,
        },
        relations=["У всех трёх чисел совпадают последние две цифры, а различается только первая цифра."],
    )


def generate_shared_payment_debt(
    *,
    rng: random.Random,
    index: int,
    difficulty_level: str,
    story_context: StoryContext | None = None,
) -> ProblemRecord:
    story = _ensure_story_context(story_context, rng)
    first_character = story.characters[0]
    second_character = story.characters[1]

    total_cost = OLYMPIAD_RANGES[difficulty_level]["payment_total"].sample(rng)
    if total_cost % 2 != 0:
        total_cost += 1
    loan_amount = OLYMPIAD_RANGES[difficulty_level]["payment_loan"].sample(rng)
    second_paid = rng.randint(max(1, total_cost // 10), max(2, total_cost // 2 - 1))
    first_paid = total_cost - second_paid
    expected_transfer = solve_shared_payment_debt(
        total_cost=total_cost,
        loan_amount=loan_amount,
        second_paid=second_paid,
    )

    if expected_transfer <= 0:
        expected_transfer = 1
        second_paid = loan_amount + total_cost // 2 - expected_transfer
        first_paid = total_cost - second_paid

    problem_text = normalize_sentence(
        f"В мире «{story.world_title}» {first_character} и {second_character} хотят вместе заплатить "
        f"{total_cost} рублей, разделив затраты поровну. Персонаж «{first_character}» дал персонажу «{second_character}» "
        f"взаймы {loan_amount} рублей. "
        f"После этого второй персонаж оплатил {second_paid} рублей, а первый — оставшиеся {first_paid} рублей. "
        f"Сколько денег должен вернуть персонаж «{second_character}» персонажу «{first_character}», "
        f"чтобы никто никому не был должен?"
    )

    assert validate_shared_payment_debt(
        total_cost=total_cost,
        loan_amount=loan_amount,
        second_paid=second_paid,
        expected_transfer=expected_transfer,
    )

    return ProblemRecord(
        code=f"OLY-PAY-{index:05d}",
        category="olympiad_logic",
        domain="olympiad_logic",
        template_name="shared_payment_debt",
        problem_text=problem_text,
        answer_text=f"{expected_transfer} рублей",
        answer_values=[expected_transfer],
        difficulty={
            "level": difficulty_level,
            "total_digits": len(str(total_cost)),
            "answer_digits": len(str(expected_transfer)),
        },
        story=_story_payload(story),
        metadata={
            "topic": "олимпиадная логика",
            "subtype": "совместная оплата и долг",
            "formula": "loan + total/2 - second_paid",
        },
        variables={
            "total_cost": total_cost,
            "loan_amount": loan_amount,
            "second_paid": second_paid,
            "first_paid": first_paid,
        },
        intermediate_values={
            "equal_share": total_cost // 2,
        },
        relations=["Нужно одновременно учесть долг по займу и выравнивание расходов до равных долей."],
    )


TEMPLATE_FACTORIES: Dict[str, Callable[..., ProblemRecord]] = {
    "digit_erasing": generate_digit_erasing,
    "birds_count": generate_birds_count,
    "three_numbers_same_suffix": generate_three_numbers_same_suffix,
    "shared_payment_debt": generate_shared_payment_debt,
}
