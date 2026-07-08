from __future__ import annotations


def run_digit_erasing_process(start_value: int, first_multiplier: int, second_multiplier: int) -> int:
    first_result = start_value * first_multiplier
    after_first_erasing = first_result // 10
    second_result = after_first_erasing * second_multiplier
    return second_result // 10


def solve_digit_erasing(
    *,
    first_multiplier: int,
    second_multiplier: int,
    final_value: int,
    search_limit: int = 10_000,
) -> list[int]:
    return [
        candidate
        for candidate in range(1, search_limit + 1)
        if run_digit_erasing_process(candidate, first_multiplier, second_multiplier) == final_value
    ]


def solve_birds_count(total_after_expansion: int) -> int:
    numerator = 4 * (total_after_expansion - 1)
    if numerator % 11 != 0:
        raise ValueError("Для таких параметров количество персонажей не является целым.")
    result = numerator // 11
    if result <= 0:
        raise ValueError("Количество персонажей должно быть положительным.")
    return result


def solve_shared_payment_debt(*, total_cost: int, loan_amount: int, second_paid: int) -> int:
    if total_cost % 2 != 0:
        raise ValueError("Общая сумма должна делиться поровну.")
    return loan_amount + total_cost // 2 - second_paid
