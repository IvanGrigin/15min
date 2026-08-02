"""Достижимость и вычёркивание: два перебора, которых нет в языке выражений.

**Лифт с двумя кнопками.** «В доме 100 этажей работают только две кнопки:
подняться на 7 и спуститься на 9. Можно ли попасть с первого этажа на нужный,
и за сколько нажатий?» Наивно кажется, что дело в наибольшем общем делителе,
но это неверно: дом ограничен снизу и сверху, и путь может существовать
по остатку, а упираться в границы. Единственный честный ответ — обход в ширину
по этажам, он же сразу даёт наименьшее число нажатий.

**Вычёркивание цифр.** «Из числа 2525252 вычёркиванием цифр получают
четырёхзначные числа. Найдите сумму всех различных таких чисел.» Здесь
важно слово «различных»: у числа с повторяющимися цифрами разные наборы
позиций дают одно и то же число, и складывать его дважды нельзя.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations


class ReachabilityError(ValueError):
    """Условие о достижимости или вычёркивании нельзя разыграть."""


def elevator_presses(
    floors: int, start: int, target: int, up: int, down: int
) -> int | None:
    """Наименьшее число нажатий, чтобы попасть со start на target.

    Возвращает None, если попасть нельзя. Обход в ширину, потому что дом
    ограничен: выйти за первый или последний этаж нельзя, и рассуждение
    через наибольший общий делитель здесь даёт неверный ответ.
    """
    if not all(isinstance(value, int) for value in (floors, start, target, up, down)):
        raise ReachabilityError("Все параметры лифта должны быть целыми числами.")
    if floors < 2 or not (1 <= start <= floors) or not (1 <= target <= floors):
        raise ReachabilityError(f"Этажи должны лежать в доме из {floors} этажей.")
    if up < 1 or down < 1:
        raise ReachabilityError("Кнопки должны двигать лифт хотя бы на этаж.")

    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        floor, presses = queue.popleft()
        if floor == target:
            return presses
        for nxt in (floor + up, floor - down):
            if 1 <= nxt <= floors and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, presses + 1))
    return None


def reachable_floors(floors: int, start: int, up: int, down: int) -> set[int]:
    """Все этажи, куда можно попасть со start."""
    seen = {start}
    queue = deque([start])
    while queue:
        floor = queue.popleft()
        for nxt in (floor + up, floor - down):
            if 1 <= nxt <= floors and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def long_rectangle_cuts(width: int, height: int) -> tuple[int, int]:
    """Сколько всего разрезов на два прямоугольника и сколько дают две длинных.

    Длинным называют прямоугольник, у которого одна сторона больше удвоенной
    другой. Разрез идёт по линии клеток — вертикально или горизонтально,
    поэтому способов ровно (width − 1) + (height − 1). Перебор нужен потому,
    что «длинность» обеих частей зависит от места разреза не монотонно:
    узкие куски у края длинные, средние — нет, и границы приходится искать.
    """
    if not isinstance(width, int) or not isinstance(height, int):
        raise ReachabilityError("Стороны прямоугольника должны быть целыми.")
    if width < 2 or height < 2:
        raise ReachabilityError("Прямоугольник должен резаться хотя бы одним способом.")

    def is_long(a: int, b: int) -> bool:
        return max(a, b) > 2 * min(a, b)

    total = both = 0
    for cut in range(1, width):
        total += 1
        if is_long(cut, height) and is_long(width - cut, height):
            both += 1
    for cut in range(1, height):
        total += 1
        if is_long(width, cut) and is_long(width, height - cut):
            both += 1
    return total, both


def deletion_results(number: int, length: int) -> set[int]:
    """Различные числа заданной длины, получаемые вычёркиванием цифр.

    Порядок оставшихся цифр сохраняется. Числа с ведущим нулём отбрасываются:
    «0525» — это не четырёхзначное число.
    """
    if not isinstance(number, int) or number < 0:
        raise ReachabilityError(f"Вычёркивать цифры можно у целого числа, получено {number!r}.")
    text = str(number)
    if not isinstance(length, int) or not 1 <= length <= len(text):
        raise ReachabilityError(
            f"Длина результата должна быть от 1 до {len(text)}, получено {length!r}.")
    found = set()
    for keep in combinations(range(len(text)), length):
        digits = "".join(text[index] for index in keep)
        if digits[0] != "0":
            found.add(int(digits))
    return found


def deletion_sum(number: int, length: int) -> int:
    """Сумма всех различных чисел, получаемых вычёркиванием.

    Слово «различных» здесь существенно: у 2525252 разные наборы позиций
    дают одно и то же число, и складывать его дважды нельзя.
    """
    return sum(deletion_results(number, length))
