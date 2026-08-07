"""Набор чисел с данной суммой, произведение которых оканчивается нулями.

Задача корпуса звучит так: «Придумайте четыре натуральных числа, сумма
которых 173, а их произведение заканчивается шестью нулями» и «Придумайте
три числа с суммой 83, произведение которых заканчивается на 4 нуля».

Верных наборов много, и источник это признаёт прямо: «в этой задаче
достаточно привести всего один пример». Поэтому ключ печатает один набор
и говорит, что подойдёт любой другой с теми же свойствами, — иначе ребёнок
с верным вторым ответом получил бы крестик. Проверка при этом остаётся
механической: свойство набора проверяется, а не сверяется с образцом.

Приём задачи — разложить 10 на двойку и пятёрку. Чтобы произведение
кончалось n нулями, среди сомножителей должно набраться n двоек и n пятёрок,
а сумма при этом обязана попасть в заданную. Степени пятёрки растут быстро,
поэтому пятёрочную часть выгодно держать в одном числе, а двоичную дробить.

Разыгрывается набор, а сумма считается по нему: прямой подбор чисел под
готовую сумму почти всегда упирался бы в то, что решения нет.
"""
from __future__ import annotations

import random

# Больше шести нулей требует сомножителей за десятки тысяч: сумма тогда
# выходит за пределы, в которых задача остаётся устной.
MIN_ZEROS = 3
MAX_ZEROS = 6
MIN_COUNT = 3
MAX_COUNT = 4
# Сколько раз пробовать собрать набор, прежде чем признать требования
# шаблона невыполнимыми.
MAX_DRAWS = 200


class ZeroProductError(ValueError):
    """Описание набора нельзя разыграть или проверить."""


def trailing_zeros(numbers: tuple[int, ...]) -> int:
    """Сколько нулей в конце произведения — без вычисления произведения.

    Произведение может быть огромным, а нули считаются по числу двоек
    и пятёрок в разложении: их минимум и есть число нулей.
    """
    twos = fives = 0
    for value in numbers:
        rest = value
        while rest % 2 == 0:
            twos += 1
            rest //= 2
        rest = value
        while rest % 5 == 0:
            fives += 1
            rest //= 5
    return min(twos, fives)


def check_shape(count: object, zeros: object) -> tuple[int, int]:
    """Проверить, что шаблон просит посильный набор."""
    if not isinstance(count, int) or isinstance(count, bool) or not MIN_COUNT <= count <= MAX_COUNT:
        raise ZeroProductError(
            f"Чисел в наборе должно быть от {MIN_COUNT} до {MAX_COUNT}, а не {count!r}.")
    if not isinstance(zeros, int) or isinstance(zeros, bool) or not MIN_ZEROS <= zeros <= MAX_ZEROS:
        raise ZeroProductError(
            f"Нулей должно быть от {MIN_ZEROS} до {MAX_ZEROS}, а не {zeros!r}.")
    return count, zeros


def is_valid(numbers: tuple[int, ...], total: int, count: int, zeros: int) -> bool:
    """Годится ли набор: столько чисел, такая сумма, столько нулей."""
    return (
        len(numbers) == count
        and all(isinstance(value, int) and value >= 1 for value in numbers)
        and sum(numbers) == total
        and trailing_zeros(numbers) >= zeros
    )


def _split(rng: random.Random, total: int, parts: int) -> list[int]:
    """Случайное разложение числа на неотрицательные слагаемые."""
    shares = [0] * parts
    for _ in range(total):
        shares[rng.randrange(parts)] += 1
    return shares


def sample_set(
    rng: random.Random, count: int, zeros: int, min_sum: int, max_sum: int
) -> tuple[int, ...]:
    """Разыграть набор из ``count`` чисел, дающий не меньше ``zeros`` нулей.

    Набор собирается, а не ищется перебором: нужные двойки и пятёрки
    раскладываются по числам случайным образом, и число получается как
    2^a · 5^b. Свободного «добора» здесь нет намеренно — при сумме 83
    и четырёх нулях все три числа обязаны нести множители, и решение
    корпуса (50, 8, 25) именно такое: двойки 1 + 3, пятёрки 2 + 2.

    Сумма считается по набору, а не задаётся заранее: подбирать числа
    под готовую сумму значило бы упираться в жеребьёвки, где решения
    не существует.
    """
    count, zeros = check_shape(count, zeros)
    if min_sum > max_sum:
        raise ZeroProductError(f"Границы суммы заданы неверно: {min_sum} > {max_sum}.")
    for _ in range(MAX_DRAWS):
        twos = _split(rng, zeros, count)
        fives = _split(rng, zeros, count)
        numbers = [2 ** two * 5 ** five for two, five in zip(twos, fives)]
        if any(value < 2 for value in numbers):
            # Число, которому не досталось ни двойки, ни пятёрки, равно единице:
            # в наборе она выглядит как отговорка и ничего не добавляет.
            continue
        total = sum(numbers)
        if not min_sum <= total <= max_sum:
            continue
        found = tuple(sorted(numbers))
        if trailing_zeros(found) >= zeros:
            return found
    raise ZeroProductError(
        f"За {MAX_DRAWS} попыток не удалось собрать набор из {count} чисел с {zeros} нулями "
        f"и суммой от {min_sum} до {max_sum}.")


def _count_factor(value: int, factor: int) -> int:
    total = 0
    while value % factor == 0:
        total += 1
        value //= factor
    return total
