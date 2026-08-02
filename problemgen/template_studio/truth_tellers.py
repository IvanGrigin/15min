"""Кто сказал правду: показания свидетелей и поиск виновного.

Задача корпуса: «После битвы со Змеем Горынычем три богатыря заявили.
Добрыня: „Змея убил Алёша“. Илья: „Змея убил Добрыня“. Алёша: „Змея убил я“.
Кто убил змея, если правду сказал только один из богатырей?»

Приём — перебор: примерить вину на каждого по очереди и посчитать, сколько
высказываний при этом оказываются истинными. Годится тот, при ком истинных
ровно столько, сколько обещано условием.

Это семейство задач в библиотеке ценно ещё и тем, что персонажи в нём
не украшение, а участники: высказывания ссылаются друг на друга по именам,
и любая тройка из любой вселенной даёт живую задачу — хоть богатыри,
хоть пираты, хоть школьники.

Главное требование к шаблону — единственность виновного. Показания могут
складываться так, что подходят двое, и тогда у задачи нет ответа, а ключ
печатается один. Такие расстановки отбрасываются.
"""
from __future__ import annotations

MAX_SPEAKERS = 6


class TruthTellerError(ValueError):
    """Набор показаний нельзя разыграть или проверить."""


def check_claims(claims: object, speakers: int) -> tuple[int, ...]:
    """Проверить показания: каждый указывает на кого-то из присутствующих."""
    if not isinstance(claims, (list, tuple)) or len(claims) != speakers:
        raise TruthTellerError(
            f"Показаний должно быть столько же, сколько говорящих ({speakers}).")
    if not 2 <= speakers <= MAX_SPEAKERS:
        raise TruthTellerError(f"Говорящих должно быть от 2 до {MAX_SPEAKERS}.")
    checked = []
    for value in claims:
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < speakers:
            raise TruthTellerError(f"Показание {value!r} указывает не на участника.")
        checked.append(value)
    return tuple(checked)


def truthful_count(claims: tuple[int, ...], culprit: int) -> int:
    """Сколько высказываний истинны, если виноват именно этот участник."""
    return sum(1 for points_at in claims if points_at == culprit)


def culprits(claims: tuple[int, ...], truthful: int) -> list[int]:
    """Все, на кого может указывать условие «правду сказали ровно n человек»."""
    return [
        culprit for culprit in range(len(claims))
        if truthful_count(claims, culprit) == truthful
    ]


def unique_culprit(claims: object, speakers: int, truthful: int) -> int:
    """Единственный виновный; иначе задача некорректна.

    Ноль подходящих означает, что условие противоречиво, а два и больше —
    что ответов несколько. И то и другое для листочка не годится.
    """
    checked = check_claims(claims, speakers)
    if not isinstance(truthful, int) or not 0 <= truthful <= speakers:
        raise TruthTellerError(f"Число правдивых должно быть от 0 до {speakers}.")
    found = culprits(checked, truthful)
    if not found:
        raise TruthTellerError(
            f"Ни при ком не выходит ровно {truthful} правдивых высказываний.")
    if len(found) > 1:
        raise TruthTellerError(
            f"Подходят сразу {len(found)} участников — виновный не определён.")
    return found[0]


def all_call_others_liars(people: int) -> int:
    """Сколько правдивцев, если каждый сказал «все остальные лгут».

    Классический случай: правдивец может быть только один. Двое правдивцев
    объявили бы лжецом друг друга, а если бы лгали все, то фраза лжеца
    «все остальные лгут» оказалась бы истинной.
    """
    if not isinstance(people, int) or people < 2:
        raise TruthTellerError("Собравшихся должно быть хотя бы двое.")
    return 1
