from __future__ import annotations

from .solvers import run_digit_erasing_process, solve_birds_count, solve_shared_payment_debt


def validate_digit_erasing(
    *,
    start_value: int,
    first_multiplier: int,
    second_multiplier: int,
    final_value: int,
) -> bool:
    return run_digit_erasing_process(start_value, first_multiplier, second_multiplier) == final_value


def validate_birds_count(*, initial_count: int, total_after_expansion: int) -> bool:
    return solve_birds_count(total_after_expansion) == initial_count


def validate_three_numbers_same_suffix(*, numbers: list[int], target_sum: int) -> bool:
    if len(numbers) != 3 or len(set(numbers)) != 3:
        return False
    if any(number < 100 or number > 999 for number in numbers):
        return False
    suffixes = {number % 100 for number in numbers}
    first_digits = {number // 100 for number in numbers}
    return len(suffixes) == 1 and len(first_digits) == 3 and sum(numbers) == target_sum


def validate_shared_payment_debt(
    *,
    total_cost: int,
    loan_amount: int,
    second_paid: int,
    expected_transfer: int,
) -> bool:
    return solve_shared_payment_debt(
        total_cost=total_cost,
        loan_amount=loan_amount,
        second_paid=second_paid,
    ) == expected_transfer
