"""Поиск момента на электронном табло по свойству его цифр.

Задачи корпуса: «На табло 10:20:30. В какое время после этого в седьмой раз
все цифры будут различными?», «На часах 11:13:33. Через какое время впервые
пять из шести цифр окажутся одинаковыми?», «На часах 11:30:00. Какое время
назад последний раз пять из шести цифр были одинаковыми?»

Приём один: идти по секундам вперёд или назад и проверять запись табло.
Формулы тут нет и быть не может — свойство касается самих цифр, а они
меняются неравномерно: после 09:59:59 идёт 10:00:00, и картина цифр
скачет. Поэтому считает перебор.

Сутки замкнуты: после 23:59:59 идёт 00:00:00. Это важно для задач, где
искомый момент лежит за полночь, и это ровно то, как ведёт себя настоящее
табло.
"""
from __future__ import annotations

DAY = 24 * 60 * 60


class ClockDigitsError(ValueError):
    """Описание поиска по табло нельзя разыграть или проверить."""


def as_text(seconds: int) -> str:
    """Запись момента на табло: 3661 секунда — это «01:01:01»."""
    seconds %= DAY
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def digits(seconds: int) -> str:
    """Шесть цифр табло без двоеточий."""
    return as_text(seconds).replace(":", "")


def _all_different(seconds: int) -> bool:
    text = digits(seconds)
    return len(set(text)) == 6


def _five_of_six_same(seconds: int) -> bool:
    text = digits(seconds)
    return any(text.count(digit) == 5 for digit in set(text))


def _all_same(seconds: int) -> bool:
    return len(set(digits(seconds))) == 1


def _four_of_six_same(seconds: int) -> bool:
    text = digits(seconds)
    return any(text.count(digit) == 4 for digit in set(text))


RULES = {
    "all_different": _all_different,
    "five_of_six_same": _five_of_six_same,
    "four_of_six_same": _four_of_six_same,
    "all_same": _all_same,
}


def check_rule(rule: object) -> str:
    """Проверить, что шаблон просит известное свойство цифр."""
    if not isinstance(rule, str) or rule not in RULES:
        raise ClockDigitsError(
            f"Неизвестное свойство цифр {rule!r}. Доступны: {', '.join(sorted(RULES))}.")
    return rule


def matches(rule: str, seconds: int) -> bool:
    """Выполняется ли свойство на этом моменте."""
    return RULES[check_rule(rule)](seconds)


def find(start: int, rule: str, occurrence: int = 1, *, forward: bool = True) -> int:
    """Момент, где свойство выполняется в occurrence-й раз от старта.

    Сам стартовый момент не считается: вопрос всегда «после этого» или
    «какое время назад», то есть отсчёт идёт со следующей секунды.
    Возвращает секунды от полуночи.
    """
    check_rule(rule)
    if not isinstance(start, int) or not 0 <= start < DAY:
        raise ClockDigitsError(f"Момент должен быть от 0 до {DAY - 1} секунд, получено {start!r}.")
    if not isinstance(occurrence, int) or occurrence < 1:
        raise ClockDigitsError(f"Номер совпадения должен быть натуральным, получено {occurrence!r}.")

    seen = 0
    step = 1 if forward else -1
    for offset in range(1, DAY + 1):
        moment = (start + step * offset) % DAY
        if matches(rule, moment):
            seen += 1
            if seen == occurrence:
                return moment
    raise ClockDigitsError(
        f"За сутки свойство {rule!r} не встретилось {occurrence} раз от момента {as_text(start)}.")


def gap(start: int, target: int, *, forward: bool = True) -> int:
    """Сколько секунд между моментами в нужную сторону."""
    return (target - start) % DAY if forward else (start - target) % DAY


def count_in_day(rule: str) -> int:
    """Сколько раз свойство встречается за сутки — нужно для отбраковки.

    Если свойство встречается слишком редко, ответ уедет за полночь и задача
    станет про переход через сутки, а не про цифры.
    """
    check_rule(rule)
    return sum(1 for second in range(DAY) if matches(rule, second))
