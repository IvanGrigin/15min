"""Отбор чисел по свойству их цифр: «однообразные», «весёлые», «грустные».

Задача корпуса выглядит так: дано правило про соседние цифры, дан список
чисел, нужно сложить те, что правилу удовлетворяют. Правило про цифры,
поэтому в языке выражений его не записать — там нет ни строк, ни обхода
разрядов. Пока решателя не было, тема жила на восьми заранее подготовленных
пакетах: список чисел и посчитанный вручную ответ прямо в JSON. Восемь
пакетов — это восемь задач навсегда, а верность ответа никем не проверялась,
потому что формулы не существовало.

Здесь Python отбирает и складывает, а JSON по-прежнему только формулирует:
как правило называется («однообразным», «весёлым», «грустным») и как оно
звучит словами — данные шаблона. Питон знает лишь идентификатор правила
и умеет его проверить.

Список правил закрыт намеренно: он же служит перечнем того, что шаблон
вправе попросить. Ссылка на неизвестное правило — ошибка шаблона, а не
молчаливо пустой отбор.
"""
from __future__ import annotations

import random

# Границы разумного: числа короче двух цифр не имеют «соседних цифр» вовсе,
# а длиннее девяти перестают читаться в списке из семи штук.
MIN_LENGTH = 2
MAX_LENGTH = 9
MAX_NUMBERS = 12
# Сколько раз пробовать добрать число нужного вида, прежде чем признать
# требования шаблона невыполнимыми. Промах здесь — дефект схемы (например,
# «пять подходящих из трёх чисел»), а не неудачный жребий.
MAX_DRAWS = 400


class DigitPredicateError(ValueError):
    """Описание отбора по цифрам нельзя разыграть или проверить."""


def _digits(value: int) -> list[int]:
    return [int(digit) for digit in str(value)]


def _has_same_parity_adjacent_pair(value: int) -> bool:
    """Есть хотя бы одна пара соседних цифр одинаковой чётности."""
    digits = _digits(value)
    return any(left % 2 == right % 2 for left, right in zip(digits, digits[1:]))


def _all_adjacent_pairs_opposite_parity(value: int) -> bool:
    """Любые две соседние цифры разной чётности — чередование без сбоев."""
    return not _has_same_parity_adjacent_pair(value)


PREDICATES = {
    "has_same_parity_adjacent_pair": _has_same_parity_adjacent_pair,
    "all_adjacent_pairs_opposite_parity": _all_adjacent_pairs_opposite_parity,
}


def check_predicate(predicate_id: object) -> str:
    """Проверить, что шаблон просит известное правило."""
    if not isinstance(predicate_id, str) or predicate_id not in PREDICATES:
        raise DigitPredicateError(
            f"Неизвестное правило отбора {predicate_id!r}. "
            f"Доступны: {', '.join(sorted(PREDICATES))}."
        )
    return predicate_id


def matches(predicate_id: str, value: int) -> bool:
    """Удовлетворяет ли число правилу."""
    return PREDICATES[check_predicate(predicate_id)](value)


def matching_sum(predicate_id: str, numbers: tuple[int, ...]) -> int:
    """Ответ задачи: сумма чисел, удовлетворяющих правилу."""
    return sum(value for value in numbers if matches(predicate_id, value))


def generate_selection(
    rng: random.Random,
    predicate_id: str,
    *,
    count: int,
    length_min: int,
    length_max: int,
    min_matching: int,
    min_rejected: int,
) -> tuple[int, ...]:
    """Собрать список чисел, в котором правило и срабатывает, и не срабатывает.

    Обе квоты обязательны и проверяются по построению. Список, где подходят
    все числа, — не задача на отбор, а задача на сложение; список, где не
    подходит ни одно, имеет ответ ноль и выглядит опечаткой. Поэтому сначала
    добираются числа под каждую квоту, а остаток — какой выпадет.
    """
    check_predicate(predicate_id)
    if not MIN_LENGTH <= length_min <= length_max <= MAX_LENGTH:
        raise DigitPredicateError(
            f"Разрядность чисел должна лежать в {MIN_LENGTH}..{MAX_LENGTH} "
            f"и не убывать, получено {length_min}..{length_max}."
        )
    if not 2 <= count <= MAX_NUMBERS:
        raise DigitPredicateError(f"Чисел в списке должно быть от 2 до {MAX_NUMBERS}.")
    if min_matching < 1 or min_rejected < 1 or min_matching + min_rejected > count:
        raise DigitPredicateError(
            f"Квоты не помещаются в список: {min_matching} подходящих и "
            f"{min_rejected} неподходящих при длине {count}."
        )

    def draw(want: bool) -> int:
        for _ in range(MAX_DRAWS):
            length = rng.randint(length_min, length_max)
            value = rng.randint(10 ** (length - 1), 10 ** length - 1)
            if matches(predicate_id, value) is want:
                return value
        raise DigitPredicateError(
            f"За {MAX_DRAWS} попыток не удалось подобрать число "
            f"{'под' if want else 'вне'} правила {predicate_id!r}."
        )

    numbers: list[int] = []
    for _ in range(min_matching):
        numbers.append(draw(True))
    for _ in range(min_rejected):
        numbers.append(draw(False))
    while len(numbers) < count:
        numbers.append(draw(rng.random() < 0.5))
    # Числа, добранные под квоты, идут первыми — без перемешивания подходящие
    # всегда стояли бы в начале списка, и правило можно было бы угадать
    # по расположению, не проверяя цифры.
    rng.shuffle(numbers)
    if len(set(numbers)) != len(numbers):
        # Повтор в списке — не ошибка арифметики, но условие выглядит
        # небрежным, а сумма перестаёт быть однозначно читаемой.
        raise DigitPredicateError("В списке оказались одинаковые числа.")
    return tuple(numbers)
