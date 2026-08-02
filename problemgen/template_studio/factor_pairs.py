"""Разложение числа на пару множителей с условием и минимальной суммой.

Задача корпуса звучит так: «Попытайтесь получить 360, перемножая два целых
сомножителя, один из которых нечётный. Таких пар несколько. Ответ —
минимальная сумма таких сомножителей».

Соль в том, что число намеренно **не** полный квадрат. Без условия минимум
суммы всегда достигается у пары, ближайшей к корню, и задача сводится
к извлечению корня. Как только на один из множителей наложено требование —
нечётность, чётность обоих, отсутствие нуля в записи, — ближайшая к корню
пара обычно не проходит, и приходится перебирать делители: 360 = 24 · 15
даёт 39, тогда как 18 · 20 = 38 не годится, потому что оба чётные.

Прежняя версия шаблона строила число как root² и печатала 2·root. Формально
ответ был верен, но задача вырождалась: ограничение на чётность ни на что
не влияло, а ответ читался как корень. Замечено преподавателем.

Перебор делителей в языке выражений невыразим, поэтому считает Python;
все формулировки условий остаются данными шаблона.
"""
from __future__ import annotations

# Числа корпуса не выходят за десятки тысяч, перебор делителей до корня
# мгновенный даже для верхней границы.
MAX_NUMBER = 100_000

CONDITIONS = {
    # Пара годится, если хотя бы один множитель нечётный.
    "one_odd": lambda a, b: a % 2 == 1 or b % 2 == 1,
    "both_even": lambda a, b: a % 2 == 0 and b % 2 == 0,
    "both_odd": lambda a, b: a % 2 == 1 and b % 2 == 1,
    # Ни в одном множителе нет цифры ноль — условие из задач про 10000.
    "no_zero_digit": lambda a, b: "0" not in str(a) and "0" not in str(b),
    "any": lambda a, b: True,
}


class FactorPairError(ValueError):
    """Условие на пару множителей нельзя разыграть или проверить."""


def check_condition(condition: object) -> str:
    """Проверить, что шаблон просит известное условие на пару."""
    if not isinstance(condition, str) or condition not in CONDITIONS:
        raise FactorPairError(
            f"Неизвестное условие на множители {condition!r}. "
            f"Доступны: {', '.join(sorted(CONDITIONS))}.")
    return condition


def pairs(number: int, condition: str) -> list[tuple[int, int]]:
    """Все пары множителей числа, удовлетворяющие условию.

    Пара берётся один раз: (a, b) с a ≤ b. Единица и само число тоже пара —
    в задачах корпуса она разрешена и иногда оказывается единственной.
    """
    check_condition(condition)
    if not isinstance(number, int) or isinstance(number, bool) or number < 2:
        raise FactorPairError(f"Раскладывать нужно натуральное число, получено {number!r}.")
    if number > MAX_NUMBER:
        raise FactorPairError(f"Число больше предела {MAX_NUMBER}.")
    keep = CONDITIONS[condition]
    found = []
    divisor = 1
    while divisor * divisor <= number:
        if number % divisor == 0:
            other = number // divisor
            if keep(divisor, other):
                found.append((divisor, other))
        divisor += 1
    return found


def min_sum(number: int, condition: str) -> int:
    """Наименьшая сумма пары множителей, удовлетворяющей условию."""
    found = pairs(number, condition)
    if not found:
        raise FactorPairError(
            f"У числа {number} нет пары множителей под условием {condition!r}.")
    return min(a + b for a, b in found)


def is_perfect_square(number: int) -> bool:
    """Полный ли квадрат — по нему шаблон отбраковывает вырожденные жеребьёвки."""
    root = int(number ** 0.5)
    for candidate in (root - 1, root, root + 1):
        if candidate >= 0 and candidate * candidate == number:
            return True
    return False


def best_pair_is_near_root(number: int, condition: str) -> bool:
    """Совпадает ли лучшая пара с ближайшей к корню — тогда условие лишнее.

    Если да, задача решается извлечением корня, и требование на множители
    ничего не добавляет. Такие жеребьёвки шаблон отбрасывает.
    """
    everything = pairs(number, "any")
    if not everything:
        return True
    closest = max(everything, key=lambda pair: pair[0])
    return closest[0] + closest[1] == min_sum(number, condition)
