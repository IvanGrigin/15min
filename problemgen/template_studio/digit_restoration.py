"""Восстановление испорченного примера на сложение и счёт вычёркиваний.

Три приёма корпуса, у которых общая природа: правильный пример испортили
известным способом, и надо вернуть исходный. Перебор здесь неизбежен —
условие задано записью числа, а не величиной, и языку выражений такое
не выразить.

Главное, ради чего написан модуль, — проверка единственности. Задача
«восстановите пример» имеет смысл, только если восстановление одно:
иначе ребёнок назовёт другое верное и получит крестик. Поэтому каждая
функция возвращает все найденные восстановления, а шаблон отбраковывает
жеребьёвки, где их больше одного.
"""
from __future__ import annotations

from datetime import date, timedelta


class RestorationError(ValueError):
    """Испорченный пример нельзя восстановить или проверить."""


def _numbers_from(digits: str, lengths: tuple[int, int, int]) -> tuple[int, int, int] | None:
    """Разрезать строку цифр на три числа; ведущий ноль делает разбор негодным."""
    first, second, third = lengths
    parts = (digits[:first], digits[first:first + second], digits[first + second:])
    if any(len(part) > 1 and part[0] == "0" for part in parts):
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


def restorations_by_swap(first: int, second: int, total: int) -> list[tuple[int, int, int]]:
    """Все способы вернуть верное сложение, поменяв местами две цифры записи.

    Меняются любые две позиции во всей записи — хоть внутри одного числа,
    хоть между разными. Перестановка одинаковых цифр ничего не меняет
    и за способ не считается.
    """
    lengths = (len(str(first)), len(str(second)), len(str(total)))
    digits = f"{first}{second}{total}"
    found: set[tuple[int, int, int]] = set()
    for left in range(len(digits)):
        for right in range(left + 1, len(digits)):
            if digits[left] == digits[right]:
                continue
            swapped = list(digits)
            swapped[left], swapped[right] = swapped[right], swapped[left]
            parsed = _numbers_from("".join(swapped), lengths)
            if parsed and parsed[0] + parsed[1] == parsed[2]:
                found.add(parsed)
    return sorted(found)


def restorations_by_replacement(first: int, second: int, total: int,
                                shown: int, hidden: int) -> list[tuple[int, int, int]]:
    """Все способы вернуть верное сложение, заменив часть цифр обратно.

    В испорченном примере каждая цифра `hidden` заменена на `shown`.
    Значит любая цифра `shown` могла быть как своей, так и подменённой,
    и перебираются все сочетания. Замена хотя бы одной цифры обязательна:
    иначе пример был бы верен и без порчи.
    """
    if shown == hidden:
        raise RestorationError("Заменяемая и подставленная цифры совпадают.")
    lengths = (len(str(first)), len(str(second)), len(str(total)))
    digits = f"{first}{second}{total}"
    places = [index for index, digit in enumerate(digits) if digit == str(shown)]
    found: set[tuple[int, int, int]] = set()
    for mask in range(1, 1 << len(places)):
        restored = list(digits)
        for offset, index in enumerate(places):
            if mask >> offset & 1:
                restored[index] = str(hidden)
        parsed = _numbers_from("".join(restored), lengths)
        if parsed and parsed[0] + parsed[1] == parsed[2]:
            found.add(parsed)
    return sorted(found)


def count_subsequences(source: str, wanted: str) -> int:
    """Сколькими способами вычеркнуть цифры так, чтобы осталось `wanted`.

    Считается по разрядам, а не перебором подмножеств: у двадцатизначного
    числа подмножеств миллион, а таблица занимает две строки.
    """
    counts = [1] + [0] * len(wanted)
    for digit in source:
        for position in range(len(wanted) - 1, -1, -1):
            if wanted[position] == digit:
                counts[position + 1] += counts[position]
    return counts[len(wanted)]


def count_palindrome_dates(first_year: int, last_year: int) -> int:
    """Сколько дат вида ддммгггг читаются одинаково в обе стороны."""
    if first_year > last_year:
        raise RestorationError(f"Пустой промежуток лет: {first_year}…{last_year}.")
    total = 0
    current = date(first_year, 1, 1)
    stop = date(last_year, 12, 31)
    while current <= stop:
        written = f"{current.day:02d}{current.month:02d}{current.year:04d}"
        if written == written[::-1]:
            total += 1
        current += timedelta(days=1)
    return total


def make_swap_puzzle(first: int, second: int, choice: int) -> tuple[int, int, int, int, int]:
    """Испортить верное сложение перестановкой двух цифр — так, чтобы вернуть его можно было одним способом.

    Пример строится от ответа: берётся верное сложение, и среди всех
    перестановок двух цифр выбирается та, после которой восстановление
    единственно. Иначе у задачи несколько верных ответов, а ключ печатается
    один.

    Возвращает показанные три числа и исходные слагаемые.
    """
    total = first + second
    lengths = (len(str(first)), len(str(second)), len(str(total)))
    digits = f"{first}{second}{total}"
    spoiled: list[tuple[int, int, int]] = []
    for left in range(len(digits)):
        for right in range(left + 1, len(digits)):
            if digits[left] == digits[right]:
                continue
            swapped = list(digits)
            swapped[left], swapped[right] = swapped[right], swapped[left]
            parsed = _numbers_from("".join(swapped), lengths)
            if not parsed or parsed[0] + parsed[1] == parsed[2]:
                continue                   # порча обязана сделать пример неверным
            if restorations_by_swap(*parsed) == [(first, second, total)]:
                spoiled.append(parsed)
    if not spoiled:
        raise RestorationError(
            f"У примера {first} + {second} нет порчи с единственным восстановлением.")
    shown = spoiled[choice % len(spoiled)]
    return shown[0], shown[1], shown[2], first, second


def make_replacement_puzzle(first: int, second: int, hidden: int,
                            shown: int) -> tuple[int, int, int]:
    """Заменить в верном сложении все цифры `hidden` на `shown`.

    Замена делается во всей записи разом, включая сумму, — иначе пример
    остался бы верным и загадки не вышло. Восстановление обязано быть
    единственным.
    """
    if hidden == shown:
        raise RestorationError("Заменяемая и подставленная цифры совпадают.")
    total = first + second
    def replaced(value: int) -> int:
        return int(str(value).replace(str(hidden), str(shown)))

    parts = (replaced(first), replaced(second), replaced(total))
    if parts == (first, second, total):
        raise RestorationError(f"В примере {first} + {second} нет цифры {hidden}.")
    if len(str(parts[2])) != len(str(total)):
        raise RestorationError("Замена изменила разрядность суммы.")
    if restorations_by_replacement(*parts, shown, hidden) != [(first, second, total)]:
        raise RestorationError("Восстановление не единственно.")
    return parts
