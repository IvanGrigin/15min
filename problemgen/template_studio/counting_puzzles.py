"""Шесть приёмов, где ответ ищется перебором, а не формулой.

Все они попали сюда по одной причине: условие задано записью числа,
набором предметов или календарём, и языку выражений такое не выразить.
Формулу пробовали — и один раз она подвела: у задачи про обезьян
`min(S/3, S − max)` даёт 52 там, где верный ответ 49, потому что при
четырёх сортах ограничение сложнее двух простых оценок. Поэтому здесь
всё считается перебором, а не выводом.

Каждая функция возвращает либо число, либо весь список решений — второе
нужно, чтобы шаблон мог отбросить жеребьёвку с неединственным ответом.
"""
from __future__ import annotations

import calendar
from itertools import combinations_with_replacement


class CountingPuzzleError(ValueError):
    """Условие нельзя разыграть или проверить перебором."""


def most_distinct_triples(counts: tuple[int, ...]) -> int:
    """Сколько троек из разных сортов можно набрать из этих запасов.

    Простые оценки — «не больше трети всего» и «не больше, чем всего без
    самого частого сорта» — обе верны, но их минимума не всегда достаточно:
    при запасах 20, 57, 52, 29 он даёт 52, а собрать удаётся только 49.
    Поэтому размер проверяется прямо: набрать m троек можно тогда и только
    тогда, когда нехватка каждого сорта покрывается пропусками, а пропусков
    ровно m — по одному на тройку.
    """
    if len(counts) < 3:
        raise CountingPuzzleError("Тройку из разных сортов не собрать меньше чем из трёх.")
    total = sum(counts)
    best = 0
    for size in range(total // 3, -1, -1):
        if sum(max(0, size - value) for value in counts) <= size:
            best = size
            break
    return best


def months_with_total_days(total: int, leap: bool = False) -> list[int]:
    """Номера месяцев, с которых три подряд дают ровно столько дней."""
    lengths = [calendar.monthrange(2024 if leap else 2025, month)[1]
               for month in range(1, 13)]
    found = []
    for first in range(1, 11):                 # три подряд внутри одного года
        if sum(lengths[first - 1:first + 2]) == total:
            found.append(first)
    return found


def products_of_two_primes(low: int, high: int, first: int = 2,
                           second: int = 3) -> list[int]:
    """Числа промежутка, которые складываются только из этих двух множителей."""
    found = set()
    power_one = 1
    while power_one <= high:
        value = power_one
        while value <= high:
            if value >= low:
                found.add(value)
            value *= second
        power_one *= first
    return sorted(found)


def star_fillings(pattern: str, divisor: int) -> list[int]:
    """Чем заменить звёздочки, чтобы число делилось нацело.

    Возвращает все получившиеся числа. Ведущий ноль не допускается:
    запись числа от этого меняет разрядность.
    """
    stars = pattern.count("*")
    if not 1 <= stars <= 4:
        raise CountingPuzzleError(f"Звёздочек должно быть от одной до четырёх: {pattern!r}.")
    found = []
    for combination in range(10 ** stars):
        digits = str(combination).zfill(stars)
        filled = pattern
        for digit in digits:
            filled = filled.replace("*", digit, 1)
        if filled[0] == "0":
            continue
        number = int(filled)
        if number % divisor == 0:
            found.append(number)
    return found


def nth_balanced_number(index: int) -> int:
    """Число с номером index среди тех, где чётных цифр столько же, сколько нечётных."""
    if index < 1:
        raise CountingPuzzleError(f"Номер должен быть натуральным, получено {index}.")
    seen = 0
    value = 9
    while seen < index:
        value += 1
        digits = [int(digit) for digit in str(value)]
        even = sum(1 for digit in digits if digit % 2 == 0)
        if even * 2 == len(digits):
            seen += 1
        if value > 2_000_000:
            raise CountingPuzzleError(f"Число с номером {index} не нашлось.")
    return value


def exact_change_ways(total: int, pieces: int, values: tuple[int, ...]) -> int:
    """Сколькими способами набрать сумму ровно заданным числом монет.

    Монеты одного достоинства неразличимы, поэтому считаются наборы,
    а не последовательности.
    """
    if pieces <= 0 or pieces > 12:
        raise CountingPuzzleError(f"Монет должно быть от одной до двенадцати, получено {pieces}.")
    return sum(1 for choice in combinations_with_replacement(values, pieces)
               if sum(choice) == total)
