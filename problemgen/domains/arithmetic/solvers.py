"""Математические решатели для арифметических шаблонов."""
from __future__ import annotations


def solve_heads_and_legs(
    legs1: int, legs2: int, total_heads: int, total_legs: int
) -> tuple[int, int] | None:
    """Решить систему: a1*x + a2*y = total_legs, x + y = total_heads.

    Returns:
        (count1, count2) или None если решение нецелое / отрицательное.
    """
    denom = legs1 - legs2
    if denom == 0:
        return None
    numerator = total_legs - legs2 * total_heads
    if numerator % denom != 0:
        return None
    count1 = numerator // denom
    count2 = total_heads - count1
    if count1 <= 0 or count2 <= 0:
        return None
    return count1, count2


def solve_ratio_sum(ratio: int, total: int) -> tuple[int, int] | None:
    """Решить: x = ratio*y, x + y = total.

    Returns:
        (count1, count2) = (ratio*y, y) или None.
    """
    if total % (ratio + 1) != 0:
        return None
    count2 = total // (ratio + 1)
    count1 = total - count2
    if count1 <= 0 or count2 <= 0:
        return None
    return count1, count2


def solve_age_friends(sum_now: int, delta: int, sum_then: int) -> int | None:
    """Решить: n * delta = sum_then - sum_now.

    Returns:
        Количество друзей n или None если решение нецелое.
    """
    diff = sum_then - sum_now
    if diff <= 0 or diff % delta != 0:
        return None
    n = diff // delta
    if n < 2:
        return None
    return n


def solve_round_robin(n: int) -> int:
    """Количество партий в круговом турнире: n*(n-1)//2."""
    return n * (n - 1) // 2


def solve_paint_cube(g_per_unit: int, h: int) -> int:
    """Краска для куба высотой h, если для куба 1 см нужно g_per_unit г.

    Площадь поверхности куба со стороной s равна 6s².
    Поэтому расход краски пропорционален h².
    """
    return g_per_unit * h * h


def solve_equal_payment(total: int, loan: int, paid2: int) -> int | None:
    """Вычислить долг: сколько второй персонаж должен вернуть первому.

    Схема:
      - оба должны заплатить по total//2
      - первый дал второму в долг loan рублей
      - второй заплатил paid2 за общий счёт
      - первый заплатил (total - paid2)

    debt = loan + total//2 - paid2

    Returns:
        Сумму долга или None если параметры некорректны.
    """
    if total % 2 != 0:
        return None
    debt = loan + total // 2 - paid2
    if debt <= 0:
        return None
    return debt
