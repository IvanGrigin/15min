"""Подсчёт чисел на промежутке с условием на цифры.

В корпусе это целое семейство: «Сколько нечётных чисел в промежутке от 215
до 983, содержащих цифру 7?», «Сколько в промежутке от 459 до 931 чисел,
не содержащих цифру 3?», «Сколько чётных чисел от 222 до 888 содержат хотя бы
одну цифру 7?».

В библиотеке уже были подсчёты по разрядности — «сколько трёхзначных чисел
не содержат цифру 5». Приём там другой: границы совпадают с границами разряда,
и всё считается умножением по позициям. Как только промежуток произвольный,
позиционная формула перестаёт работать: у 215 и 983 разное число «свободных»
разрядов, и края приходится разбирать отдельно.

Поэтому здесь честный перебор. Промежутки в задачах корпуса не выходят за
несколько тысяч, перебор мгновенный, а формула, которую пришлось бы выводить,
заняла бы страницу и не проверялась бы ничем.

Правила подобраны так, чтобы ответ никогда не был ни нулём, ни всем
промежутком целиком: и то и другое означает, что условие ничего не отбирает.
"""
from __future__ import annotations

# Промежутки корпуса не длиннее нескольких тысяч; предел стоит затем, чтобы
# случайный жребий не превратил генерацию задачи в долгий счёт.
MAX_SPAN = 20_000

PARITIES = {
    "any": lambda value: True,
    "even": lambda value: value % 2 == 0,
    "odd": lambda value: value % 2 == 1,
}
DIGIT_RULES = {
    "any": lambda text, digit: True,
    "contains": lambda text, digit: digit in text,
    "without": lambda text, digit: digit not in text,
}


class RangeCountError(ValueError):
    """Описание подсчёта на промежутке нельзя разыграть или проверить."""


def check_rule(parity: object, digit_rule: object) -> tuple[str, str]:
    """Проверить, что шаблон просит известные правила отбора."""
    if not isinstance(parity, str) or parity not in PARITIES:
        raise RangeCountError(
            f"Неизвестная чётность {parity!r}. Доступны: {', '.join(sorted(PARITIES))}.")
    if not isinstance(digit_rule, str) or digit_rule not in DIGIT_RULES:
        raise RangeCountError(
            f"Неизвестное правило по цифре {digit_rule!r}. "
            f"Доступны: {', '.join(sorted(DIGIT_RULES))}.")
    return parity, digit_rule


def count_in_range(
    low: int, high: int, *, parity: str, digit_rule: str, digit: int,
    multiple_of: int = 1,
) -> int:
    """Сколько чисел промежутка удовлетворяют всем условиям сразу.

    Промежуток берётся замкнутым: «от 215 до 983» в задачах корпуса включает
    оба конца. Где источник говорит «больше 215, но меньше 983», шаблон
    передаёт уже сдвинутые границы — это его дело, а не решателя.
    """
    check_rule(parity, digit_rule)
    if not isinstance(low, int) or not isinstance(high, int) or low > high:
        raise RangeCountError(f"Промежуток задан неверно: от {low!r} до {high!r}.")
    if high - low > MAX_SPAN:
        raise RangeCountError(f"Промежуток длиннее {MAX_SPAN} — перебор слишком долгий.")
    if not isinstance(digit, int) or not 0 <= digit <= 9:
        raise RangeCountError(f"Цифра должна быть от 0 до 9, получено {digit!r}.")
    if not isinstance(multiple_of, int) or multiple_of < 1:
        raise RangeCountError(f"Делитель должен быть натуральным, получено {multiple_of!r}.")

    keep_parity = PARITIES[parity]
    keep_digit = DIGIT_RULES[digit_rule]
    mark = str(digit)
    return sum(
        1 for value in range(low, high + 1)
        if keep_parity(value) and value % multiple_of == 0 and keep_digit(str(value), mark)
    )


def span_size(low: int, high: int, *, parity: str, multiple_of: int = 1) -> int:
    """Сколько чисел промежутка проходят отбор до условия на цифру.

    Нужно шаблону, чтобы отбраковать вырожденные случаи: если условие на цифру
    оставляет всё или не оставляет ничего, задача не про цифры.
    """
    keep_parity = PARITIES[parity]
    return sum(
        1 for value in range(low, high + 1)
        if keep_parity(value) and value % multiple_of == 0
    )
