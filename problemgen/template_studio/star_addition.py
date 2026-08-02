"""Сложение со звёздочками: «*54** + *82** = 10*793».

Задача корпуса: часть цифр в столбике сложения закрыта звёздочками, нужно
найти сумму всех закрытых цифр. Соль в том, что сами цифры чаще всего
восстановить нельзя — а их сумма определена однозначно.

Для *54** + *82** = 10*793 разбор такой. Из разряда сотен: 4 + 2 плюс
перенос даёт 7, значит перенос равен единице, а дальше он не идёт. Из
тысяч: 5 + 8 = 13, поэтому закрытая цифра суммы — тройка, и перенос идёт
дальше. Из десятков тысяч: закрытые цифры слагаемых в сумме дают девять.
Из десятков: они дают восемнадцать, из единиц — тринадцать. Итого
9 + 18 + 13 + 3 = 43, и это единственный возможный ответ, хотя сами
слагаемые могут быть разными.

Отсюда главное требование к шаблону: сумма закрытых цифр обязана быть
единственной. Если разные расстановки дают разные суммы, задача
некорректна, и такие маски отбрасываются.

Перебор устроен экономно: перебираются первое слагаемое и сумма, а второе
слагаемое получается вычитанием и проверяется по своей маске. Для типичных
масок это десять-двадцать тысяч вариантов вместо миллиона.
"""
from __future__ import annotations

from itertools import product

STAR = "*"
MAX_STARS_PER_NUMBER = 4


class StarAdditionError(ValueError):
    """Маску сложения нельзя разыграть или проверить."""


def check_mask(mask: object, name: str) -> str:
    """Проверить, что маска — строка из цифр и звёздочек без ведущего нуля."""
    if not isinstance(mask, str) or not mask or len(mask) > 7:
        raise StarAdditionError(f"{name}: маска должна быть строкой длиной до семи знаков.")
    if any(char != STAR and not char.isdigit() for char in mask):
        raise StarAdditionError(f"{name}: в маске допустимы только цифры и звёздочки.")
    if mask[0] == "0":
        raise StarAdditionError(f"{name}: число не может начинаться с нуля.")
    if mask.count(STAR) > MAX_STARS_PER_NUMBER:
        raise StarAdditionError(f"{name}: не больше {MAX_STARS_PER_NUMBER} звёздочек в числе.")
    return mask


def candidates(mask: str) -> list[int]:
    """Все числа, подходящие под маску. Ведущий ноль запрещён."""
    positions = [index for index, char in enumerate(mask) if char == STAR]
    if not positions:
        return [int(mask)]
    found = []
    for filling in product(range(10), repeat=len(positions)):
        chars = list(mask)
        for index, digit in zip(positions, filling):
            chars[index] = str(digit)
        if chars[0] == "0":
            continue
        found.append(int("".join(chars)))
    return found


def _fits(mask: str, value: int) -> bool:
    text = str(value)
    if len(text) != len(mask):
        return False
    return all(char == STAR or char == digit for char, digit in zip(mask, text))


def _hidden_digit_sum(mask: str, value: int) -> int:
    text = str(value)
    return sum(int(digit) for char, digit in zip(mask, text) if char == STAR)


def solutions(first: str, second: str, total: str) -> list[tuple[int, int, int]]:
    """Все тройки чисел, подходящие под маски и дающие верное сложение."""
    check_mask(first, "первое слагаемое")
    check_mask(second, "второе слагаемое")
    check_mask(total, "сумма")
    found = []
    for left in candidates(first):
        for whole in candidates(total):
            right = whole - left
            if right > 0 and _fits(second, right):
                found.append((left, right, whole))
    return found


def hidden_sums(first: str, second: str, total: str) -> set[int]:
    """Все возможные суммы закрытых цифр — по одной на каждое решение."""
    return {
        _hidden_digit_sum(first, left) + _hidden_digit_sum(second, right)
        + _hidden_digit_sum(total, whole)
        for left, right, whole in solutions(first, second, total)
    }


def unique_hidden_sum(first: str, second: str, total: str) -> int:
    """Единственная сумма закрытых цифр; иначе задача некорректна.

    Разные расстановки цифр — это нормально и даже нужно: восстановить их
    нельзя, и в этом смысл задачи. А вот разные суммы означают, что верных
    ответов несколько, а ключ печатается один.
    """
    sums = hidden_sums(first, second, total)
    if not sums:
        raise StarAdditionError("Ни одна расстановка цифр не даёт верного сложения.")
    if len(sums) > 1:
        raise StarAdditionError(
            f"Сумма закрытых цифр не определена однозначно: {sorted(sums)}.")
    return sums.pop()


def mask_number(value: int, positions: tuple[int, ...]) -> str:
    """Закрыть звёздочками указанные позиции числа, считая слева от нуля."""
    chars = list(str(value))
    for index in positions:
        if not 0 <= index < len(chars):
            raise StarAdditionError(f"В числе {value} нет позиции {index}.")
        chars[index] = STAR
    return "".join(chars)
