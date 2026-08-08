"""Наименьшая стоимость покупки, когда товар продаётся только пачками.

Задача свода: «Курс витаминов нужно принимать по 2–3 таблетки 3–4 раза в
день в течение 3–5 недель. Пачка из 120 таблеток стоит 239 рублей, пачка
из 50 таблеток — 113 рублей. Какое наименьшее число рублей заведомо
придётся потратить?»

Ловушка здесь ровно одна, и она не в арифметике курса. Большая пачка
выгоднее в пересчёте на таблетку (239/120 против 113/50), но покупать
только большие пачки — не лучший ход: на 126 таблеток три маленькие
пачки (339 рублей) дешевле, чем большая с маленькой (352 рубля).
Поэтому «взять как можно больше выгодных пачек, остаток добрать» —
неверный жадный ответ, и никакой формулы тут нет: нужен перебор.

Перебор в языке выражений шаблона невыразим — там нет ни цикла, ни
списков. Считает Python, формулировки остаются данными шаблона.
"""
from __future__ import annotations

MAX_NEED = 20000


class PackPurchaseError(ValueError):
    """Набор пачек нельзя разыграть или проверить."""


def check_packs(packs: object) -> tuple[tuple[int, int], ...]:
    """Проверить, что пачки заданы парами «сколько таблеток, сколько рублей»."""
    if not isinstance(packs, (list, tuple)) or not packs:
        raise PackPurchaseError(f"Нужен непустой список пачек, а не {packs!r}.")
    checked: list[tuple[int, int]] = []
    for item in packs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise PackPurchaseError(f"Пачка описывается парой (размер, цена), а не {item!r}.")
        size, price = item
        for value in (size, price):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise PackPurchaseError(f"Размер и цена пачки — целые положительные, а не {item!r}.")
        checked.append((int(size), int(price)))
    if len({size for size, _ in checked}) != len(checked):
        raise PackPurchaseError(f"Пачки одного размера с разной ценой бессмысленны: {packs!r}.")
    return tuple(sorted(checked))


def min_cost(need: object, packs: object) -> int:
    """Наименьшая сумма, за которую можно купить хотя бы ``need`` таблеток.

    «Хотя бы» — это важно: лишние таблетки разрешены, и часто именно
    покупка с запасом оказывается дешевле точной. Считается динамикой по
    числу таблеток; хвост длиной в самую большую пачку добавлен как раз
    затем, чтобы перекупить было можно.
    """
    checked = check_packs(packs)
    if not isinstance(need, int) or isinstance(need, bool) or need <= 0:
        raise PackPurchaseError(f"Нужное число таблеток — целое положительное, а не {need!r}.")
    if need > MAX_NEED:
        raise PackPurchaseError(f"Курс из {need} таблеток слишком велик для перебора.")
    limit = need + max(size for size, _ in checked)
    best = [0] + [None] * limit
    for amount in range(1, limit + 1):
        for size, price in checked:
            previous = best[max(0, amount - size)]
            if previous is None:
                continue
            candidate = previous + price
            if best[amount] is None or candidate < best[amount]:
                best[amount] = candidate
    found = [value for value in best[need:] if value is not None]
    if not found:
        raise PackPurchaseError(f"Пачками {checked} нельзя набрать {need} таблеток.")
    return min(found)


def greedy_cost(need: object, packs: object) -> int:
    """Сколько выйдет у того, кто берёт большие пачки, пока хватает.

    Нужен не для ответа, а для отбора жеребьёвок: задача интересна лишь
    там, где жадность промахивается. Шаблон требует, чтобы это число
    отличалось от верного.
    """
    checked = check_packs(packs)
    if not isinstance(need, int) or isinstance(need, bool) or need <= 0:
        raise PackPurchaseError(f"Нужное число таблеток — целое положительное, а не {need!r}.")
    left, total = need, 0
    for size, price in sorted(checked, key=lambda pack: (price_per_tablet(pack), -pack[0])):
        while left >= size:
            left -= size
            total += price
    if left > 0:
        cheapest_small = min(checked, key=lambda pack: pack[1])
        total += cheapest_small[1]
    return total


def price_per_tablet(pack: tuple[int, int]) -> float:
    """Цена одной таблетки в пачке — по ней жадный покупатель и выбирает."""
    size, price = pack
    return price / size


def course_tablets(dose: int, times: int, weeks: int) -> int:
    """Сколько таблеток съедает курс: доза × приёмов в день × дней."""
    for value in (dose, times, weeks):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise PackPurchaseError(f"Параметры курса — целые положительные, а не {value!r}.")
    return dose * times * weeks * 7
