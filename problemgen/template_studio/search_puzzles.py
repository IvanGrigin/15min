"""Три задачи, где ответ ищут перебором: гири, цепочка цифр, наименьшее N.

**Гири на двух чашах.** «Имеются гири 1, 2 и 9 кг. Какие веса можно взвесить,
если класть гири на обе чаши?» Каждая гиря участвует одним из трёх способов:
лежит рядом с грузом, лежит напротив него или не используется. Отсюда 3^k
комбинаций, и перебрать их — самый честный способ: закономерность в наборе
достижимых весов зависит от самих гирь и общей формулы не имеет.

**Цепочка последних цифр.** «В последовательности 1, 2, 2, 4, 8, 2, 6, …
каждая цифра равна последней цифре произведения двух предыдущих. Какая цифра
стоит на 2021-м месте?» Цифр всего десять, пар — сто, поэтому цепочка обязана
зациклиться, и вопрос сводится к поиску предпериода и периода.

**Наименьшее N с условием на цифры.** «Числа N, N + 239 и N + 1000 вместе
содержат ровно три семёрки. Найдите наименьшее такое N.» Условие про запись,
а не про величину, поэтому перебор снизу — единственный способ.
"""
from __future__ import annotations

from itertools import product

MAX_WEIGHTS = 5
MAX_SEARCH = 200_000


class SearchPuzzleError(ValueError):
    """Условие перебора нельзя разыграть или проверить."""


def weighable(weights: tuple[int, ...]) -> list[int]:
    """Все веса, которые можно отмерить гирями на весах с двумя чашами.

    Гиря либо кладётся к грузу (минус), либо на другую чашу (плюс), либо
    остаётся в стороне. Ноль не считается: «взвесить ноль» бессмысленно.
    """
    if not weights or len(weights) > MAX_WEIGHTS:
        raise SearchPuzzleError(f"Гирь должно быть от одной до {MAX_WEIGHTS}.")
    if any(not isinstance(value, int) or value < 1 for value in weights):
        raise SearchPuzzleError("Каждая гиря — натуральное число килограммов.")
    found = {
        abs(sum(weight * sign for weight, sign in zip(weights, signs)))
        for signs in product((-1, 0, 1), repeat=len(weights))
    }
    return sorted(found - {0})


def digit_chain(first: int, second: int, operation: str, position: int) -> int:
    """Цифра на заданном месте цепочки последних цифр.

    Цепочка задаётся двумя первыми цифрами и действием: каждая следующая —
    последняя цифра произведения или суммы двух предыдущих. Пар цифр всего
    сто, поэтому цепочка непременно зацикливается; место находится по
    предпериоду и периоду, а не прямым счётом до двухтысячного члена.
    """
    if operation not in {"mul", "add"}:
        raise SearchPuzzleError(f"Действие должно быть 'mul' или 'add', получено {operation!r}.")
    for value in (first, second):
        if not isinstance(value, int) or not 0 <= value <= 9:
            raise SearchPuzzleError(f"Начальные члены — цифры, получено {value!r}.")
    if not isinstance(position, int) or position < 1:
        raise SearchPuzzleError(f"Место должно быть натуральным, получено {position!r}.")

    sequence = [first, second]
    seen: dict[tuple[int, int], int] = {(first, second): 0}
    while len(sequence) < position:
        previous, last = sequence[-2], sequence[-1]
        nxt = (previous * last if operation == "mul" else previous + last) % 10
        sequence.append(nxt)
        key = (last, nxt)
        index = len(sequence) - 2
        if key in seen:
            start = seen[key]
            period = index - start
            return sequence[start + (position - 1 - start) % period]
        seen[key] = index
    return sequence[position - 1]


def smallest_with_digit_count(
    shifts: tuple[int, ...], digit: int, wanted: int, limit: int = MAX_SEARCH
) -> int:
    """Наименьшее N, при котором N и N + shift вместе содержат ровно `wanted` таких цифр.

    Условие про запись числа, а не про его величину, поэтому идём снизу
    и проверяем каждое: закономерности, по которой можно было бы прыгнуть
    сразу к ответу, тут нет.
    """
    if not isinstance(digit, int) or not 0 <= digit <= 9:
        raise SearchPuzzleError(f"Цифра должна быть от 0 до 9, получено {digit!r}.")
    if not isinstance(wanted, int) or wanted < 1:
        raise SearchPuzzleError("Искомых цифр должно быть хотя бы одна.")
    mark = str(digit)
    for value in range(1, limit):
        written = str(value) + "".join(str(value + shift) for shift in shifts)
        if written.count(mark) == wanted:
            return value
    raise SearchPuzzleError(
        f"До {limit} не нашлось числа с ровно {wanted} цифрами {digit}.")
