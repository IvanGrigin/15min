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


def _statement_holds(statement: object, winner: int, people: int) -> bool:
    """Истинно ли высказывание, если победил именно этот участник.

    Высказывание — пара (на кого указывает, утверждение или отрицание):
    «больше всех решил третий» или «нет, не первая». Отрицание нужно
    отдельным полем, потому что «не ты» — это не указание на кого-то
    другого: оно истинно сразу при нескольких победителях.
    """
    if (not isinstance(statement, (list, tuple)) or len(statement) != 2):
        raise TruthTellerError(
            f"Высказывание {statement!r} должно быть парой [на кого, правда ли].")
    points_at, positive = statement
    if not isinstance(points_at, int) or isinstance(points_at, bool):
        raise TruthTellerError(f"Высказывание указывает не на участника: {points_at!r}.")
    if not 0 <= points_at < people:
        raise TruthTellerError(f"Высказывание указывает за пределы компании: {points_at!r}.")
    if not isinstance(positive, bool):
        raise TruthTellerError(f"Утверждение или отрицание задаётся true/false, дано {positive!r}.")
    return (points_at == winner) if positive else (points_at != winner)


def unique_winner(speakers: object, statements: object, people: int) -> int:
    """Единственный, кто мог решить больше всех, если правду сказал только он.

    Условие задачи: победитель сказал правду, а все остальные солгали.
    Говорить может кто угодно и сколько угодно раз, поэтому проверка идёт
    по говорящему: все фразы победителя истинны, все чужие — ложны.

    Ответ обязан быть единственным. Набор реплик легко составить так, что
    подойдут двое или ни один, и тогда у задачи нет ответа, а ключ
    печатается один.
    """
    if not isinstance(speakers, (list, tuple)) or not isinstance(statements, (list, tuple)):
        raise TruthTellerError("Говорящие и их реплики задаются списками.")
    if len(speakers) != len(statements):
        raise TruthTellerError(
            f"Реплик {len(statements)}, а говорящих при них {len(speakers)}.")
    if not 2 <= people <= MAX_SPEAKERS:
        raise TruthTellerError(f"Спорящих должно быть от 2 до {MAX_SPEAKERS}.")
    for speaker in speakers:
        if not isinstance(speaker, int) or isinstance(speaker, bool) or not 0 <= speaker < people:
            raise TruthTellerError(f"Реплику произносит не участник спора: {speaker!r}.")

    fits = [
        winner for winner in range(people)
        if all(
            _statement_holds(statement, winner, people) == (speaker == winner)
            for speaker, statement in zip(speakers, statements)
        )
    ]
    if not fits:
        raise TruthTellerError("Ни при ком реплики не складываются: правду говорил бы не победитель.")
    if len(fits) > 1:
        raise TruthTellerError(f"Подходят сразу {len(fits)} участников — победитель не определён.")
    return fits[0]


# Перебор расстановок — это 2^n, поэтому за столом не больше четырнадцати
# человек. Для высказывания «все остальные лгут» ответ известен аналитически,
# и там ограничения нет.
MAX_CIRCLE = 14

CIRCLE_CLAIMS = ("next_k_liars", "one_neighbour_liar", "all_others_liars")


def _claim_holds(seats: tuple[bool, ...], index: int, kind: str, span: int) -> bool:
    """Истинно ли высказывание сидящего, если расстановка именно такая."""
    people = len(seats)
    if kind == "next_k_liars":
        return all(not seats[(index + step) % people] for step in range(1, span + 1))
    if kind == "one_neighbour_liar":
        left = seats[(index - 1) % people]
        right = seats[(index + 1) % people]
        return left != right
    return all(not seats[other] for other in range(people) if other != index)


def circle_truth_counts(people: int, kind: str, span: int = 0) -> set[int]:
    """Сколько правдивцев может быть за столом при таких высказываниях.

    Правдивец говорит истину, лжец — ложь, поэтому расстановка годится, если
    у каждого высказывание совпадает с его собственной природой. Перебираются
    все расстановки: короткого правила, которое давало бы ответ сразу,
    для круга нет.
    """
    if kind not in CIRCLE_CLAIMS:
        raise TruthTellerError(
            f"Неизвестное высказывание {kind!r}. Доступны: {', '.join(CIRCLE_CLAIMS)}.")
    if not isinstance(people, int) or people < 3:
        raise TruthTellerError("За столом должно быть хотя бы трое.")
    if kind == "all_others_liars":
        # Двое правдивцев объявили бы лжецом друг друга; если бы лгали все,
        # фраза лжеца оказалась бы истинной. Значит правдивец ровно один.
        return {1}
    if people > MAX_CIRCLE:
        raise TruthTellerError(f"За столом не больше {MAX_CIRCLE} человек: перебор 2^n.")
    if kind == "next_k_liars" and not 1 <= span < people:
        raise TruthTellerError(f"Соседей в высказывании должно быть от 1 до {people - 1}.")

    found = set()
    for mask in range(1 << people):
        seats = tuple(bool(mask >> index & 1) for index in range(people))
        if all(seats[index] == _claim_holds(seats, index, kind, span)
               for index in range(people)):
            found.add(sum(seats))
    return found


def unique_liar_count(people: int, kind: str, span: int = 0) -> int:
    """Единственное возможное число лжецов; иначе задача некорректна."""
    counts = circle_truth_counts(people, kind, span)
    if not counts:
        raise TruthTellerError("Ни одна расстановка не подходит под высказывания.")
    if len(counts) > 1:
        raise TruthTellerError(
            f"Подходят разные расстановки: правдивцев может быть {sorted(counts)}.")
    return people - counts.pop()


def all_call_others_liars(people: int) -> int:
    """Сколько правдивцев, если каждый сказал «все остальные лгут».

    Классический случай: правдивец может быть только один. Двое правдивцев
    объявили бы лжецом друг друга, а если бы лгали все, то фраза лжеца
    «все остальные лгут» оказалась бы истинной.
    """
    if not isinstance(people, int) or people < 2:
        raise TruthTellerError("Собравшихся должно быть хотя бы двое.")
    return 1
