"""Цепочка цифр, где каждая следующая — последняя цифра действия над двумя предыдущими.

Задача корпуса выглядит так: «В последовательности 1, 2, 2, 4, 8, 2, 6, …
каждая цифра равна последней цифре произведения предыдущих двух цифр.
Как видно, на 4-м месте стоит цифра 4. А какая цифра стоит на 2021-м месте?»

Приём — не арифметика, а наблюдение: пара соседних цифр полностью задаёт всё
дальнейшее, пар всего сто, поэтому цепочка обязана зациклиться, и притом
быстро. Дальше нужно найти предпериод и период и взять остаток.

В языке выражений этого не записать: там нет ни цикла, ни памяти о том, какие
пары уже встречались. Поэтому считает Python — ровно так же, как это делают
`alphabet_order.py` и `digit_predicates.py`. JSON по-прежнему только
формулирует: как называется действие («произведения», «суммы»), с какого места
спрашивают и какое место показано в примере.

Список действий закрыт намеренно: он же служит перечнем того, что шаблон
вправе попросить. Ссылка на неизвестное действие — дефект шаблона, а не
молчаливо пустая цепочка.
"""
from __future__ import annotations

# Длиннее ста шагов цепочка из пар цифр быть не может: пар ровно сто,
# и сто первый шаг обязан повторить какую-то из уже виденных.
MAX_STEPS = 200
# Показывать в условии меньше пяти цифр бессмысленно: по трём правило
# угадывается неоднозначно.
MIN_PREFIX = 5
MAX_PREFIX = 9

RULES = {
    "product": lambda first, second: (first * second) % 10,
    "sum": lambda first, second: (first + second) % 10,
}


class DigitRecurrenceError(ValueError):
    """Описание цепочки цифр нельзя разыграть или проверить."""


def check_rule(rule: object) -> str:
    """Проверить, что шаблон просит известное действие."""
    if not isinstance(rule, str) or rule not in RULES:
        raise DigitRecurrenceError(
            f"Неизвестное правило цепочки {rule!r}. Доступны: {', '.join(sorted(RULES))}.")
    return rule


def _check_start(first: object, second: object) -> tuple[int, int]:
    for value in (first, second):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
            raise DigitRecurrenceError(f"Начальная цифра должна быть от 0 до 9, а не {value!r}.")
    return int(first), int(second)  # type: ignore[arg-type]


def prefix(first: int, second: int, rule: str, length: int) -> list[int]:
    """Первые ``length`` цифр цепочки — то, что печатается в условии."""
    check_rule(rule)
    first, second = _check_start(first, second)
    if not isinstance(length, int) or isinstance(length, bool) or not MIN_PREFIX <= length <= MAX_PREFIX:
        raise DigitRecurrenceError(
            f"Длина показанного начала должна быть от {MIN_PREFIX} до {MAX_PREFIX}, а не {length!r}.")
    chain = [first, second]
    while len(chain) < length:
        chain.append(RULES[rule](chain[-2], chain[-1]))
    return chain


def digit_at(first: int, second: int, rule: str, position: int) -> int:
    """Цифра на ``position``-м месте: позиции нумеруются с единицы.

    Считается через предпериод и период, а не прямым проходом до 2021-го
    шага: цепочка из пар цифр обязана зациклиться не позже сотого шага,
    и вся задача именно в том, чтобы это заметить.
    """
    check_rule(rule)
    first, second = _check_start(first, second)
    if not isinstance(position, int) or isinstance(position, bool) or position < 1:
        raise DigitRecurrenceError(f"Номер места должен быть натуральным, а не {position!r}.")

    chain = [first, second]
    seen: dict[tuple[int, int], int] = {(first, second): 0}
    while len(chain) <= MAX_STEPS:
        if position <= len(chain):
            return chain[position - 1]
        chain.append(RULES[rule](chain[-2], chain[-1]))
        pair = (chain[-2], chain[-1])
        start = seen.get(pair)
        if start is None:
            seen[pair] = len(chain) - 2
            continue
        # Пара повторилась: цепочка от start до len(chain)-2 повторяется вечно.
        period = (len(chain) - 2) - start
        return chain[start + (position - 1 - start) % period]
    raise DigitRecurrenceError("Цепочка не зациклилась за отведённые шаги.")


def period_length(first: int, second: int, rule: str) -> int:
    """Длина периода — по ней шаблон отбраковывает вырожденные цепочки.

    Период единица означает, что цифра с какого-то места не меняется вовсе:
    ответ виден без всякого счёта, и задача исчезает.
    """
    check_rule(rule)
    first, second = _check_start(first, second)
    chain = [first, second]
    seen: dict[tuple[int, int], int] = {(first, second): 0}
    while len(chain) <= MAX_STEPS:
        chain.append(RULES[rule](chain[-2], chain[-1]))
        pair = (chain[-2], chain[-1])
        start = seen.get(pair)
        if start is None:
            seen[pair] = len(chain) - 2
            continue
        return (len(chain) - 2) - start
    raise DigitRecurrenceError("Цепочка не зациклилась за отведённые шаги.")
