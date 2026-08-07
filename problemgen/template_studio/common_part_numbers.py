"""Числа, отличающиеся друг от друга ровно одной цифрой.

Задача корпуса звучит так: «Придумайте три различных трёхзначных числа
с суммой 817, которые отличаются друг от друга только первой цифрой».
Девять задач-близнецов, и это самая большая непокрытая группа свода.

Приём — разложить сумму на общую часть и на цифры. Если числа отличаются
только первой цифрой, каждое равно d·100 + tail с общим хвостом; сумма
трёх равна 100·(d₁+d₂+d₃) + 3·tail. Отсюда хвост находится по остатку
суммы, а цифры — по частному. Ни перебора, ни угадывания: два деления.

Кажется, что примеров много, но для 817 он ровно один — 139, 239, 439.
Из 1900 достижимых сумм единственное решение дают 400, и шаблон берёт
только их: тогда ответ печатается целиком и честен.

Перебор в языке выражений невыразим — там нет ни цикла, ни списков,
поэтому решения ищет Python, а формулировки остаются данными шаблона.
"""
from __future__ import annotations

import itertools

MIN_COUNT = 3
MAX_COUNT = 4
MIN_LENGTH = 3
MAX_LENGTH = 4
POSITIONS = ("first", "last")


class CommonPartError(ValueError):
    """Описание набора чисел нельзя разыграть или проверить."""


def check_shape(count: object, length: object, position: object) -> tuple[int, int, str]:
    """Проверить, что шаблон просит посильный набор."""
    if not isinstance(count, int) or isinstance(count, bool) or not MIN_COUNT <= count <= MAX_COUNT:
        raise CommonPartError(
            f"Чисел в наборе должно быть от {MIN_COUNT} до {MAX_COUNT}, а не {count!r}.")
    if not isinstance(length, int) or isinstance(length, bool) or not MIN_LENGTH <= length <= MAX_LENGTH:
        raise CommonPartError(
            f"Разрядность должна быть от {MIN_LENGTH} до {MAX_LENGTH}, а не {length!r}.")
    if not isinstance(position, str) or position not in POSITIONS:
        raise CommonPartError(
            f"Позиция различающейся цифры — {' или '.join(POSITIONS)}, а не {position!r}.")
    return count, length, position


def build(digits: tuple[int, ...], common: int, length: int, position: str) -> list[int]:
    """Собрать набор чисел по различающимся цифрам и общей части."""
    if position == "first":
        step = 10 ** (length - 1)
        return sorted(digit * step + common for digit in digits)
    return sorted(common * 10 + digit for digit in digits)


def solutions(total: int, count: int, length: int, position: str) -> list[list[int]]:
    """Все наборы из ``count`` чисел с такой суммой.

    Различающиеся цифры обязаны быть разными: в источнике числа названы
    различными. Для первой позиции цифра не бывает нулём, для последней —
    бывает, и это меняет и перебор, и ответ.
    """
    count, length, position = check_shape(count, length, position)
    found: list[list[int]] = []
    if position == "first":
        common_high = 10 ** (length - 1)
        for digits in itertools.combinations(range(1, 10), count):
            rest = total - sum(digits) * common_high
            if rest < 0 or rest % count:
                continue
            common = rest // count
            if 0 <= common < common_high:
                found.append(build(digits, common, length, position))
    else:
        low, high = 10 ** (length - 2), 10 ** (length - 1)
        for digits in itertools.combinations(range(10), count):
            rest = total - sum(digits)
            if rest < 0 or rest % (count * 10):
                continue
            common = rest // (count * 10)
            if low <= common < high:
                found.append(build(digits, common, length, position))
    return sorted(found)
