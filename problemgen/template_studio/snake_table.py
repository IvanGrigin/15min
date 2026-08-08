"""Таблица, занумерованная змейкой, и отметки по одной в строке и столбце.

Задача свода: «В таблице 5 × 5, клетки которой пронумерованы змейкой,
надо отметить несколько клеток так, чтобы в каждой строке и в каждом
столбце была отмечена ровно одна. Кирилл отметил клетки 1, 13, 19 и ещё
две. Чему может быть равна сумма номеров этих двух клеток?»

Приём двойной. Сначала номер надо превратить в клетку: нумерация идёт
змейкой, поэтому в нечётных строках номер растёт слева направо, а в
чётных — справа налево, и «19» в таблице 5 × 5 стоит не там, где его
ищут по делению с остатком. Потом остаётся комбинаторика: занятые строки
и столбцы вычёркиваются, а свободные надо составить в пары — вариантов
столько, сколько перестановок оставшегося квадрата.

Ответов обычно несколько, и это часть задачи: источник спрашивает «чему
может быть равна». Поэтому возвращается список сумм, а не одна.

Перестановки в языке выражений невыразимы, поэтому считает Python.
"""
from __future__ import annotations

import itertools

MIN_SIZE = 4
MAX_SIZE = 7


class SnakeTableError(ValueError):
    """Расстановку отметок нельзя разыграть или проверить."""


def check_size(size: object) -> int:
    """Проверить сторону таблицы."""
    if not isinstance(size, int) or isinstance(size, bool) or not MIN_SIZE <= size <= MAX_SIZE:
        raise SnakeTableError(f"Сторона таблицы — от {MIN_SIZE} до {MAX_SIZE}, а не {size!r}.")
    return size


def cell_value(size: int, row: int, column: int) -> int:
    """Номер клетки на пересечении строки и столбца, нумерация с единицы.

    Нечётные строки идут слева направо, чётные — справа налево: это и есть
    змейка. Ошибиться здесь легче всего, поэтому обратное преобразование
    написано отдельно и сверяется с прямым.
    """
    size = check_size(size)
    if not 1 <= row <= size or not 1 <= column <= size:
        raise SnakeTableError(f"Клетка ({row}, {column}) выходит за таблицу {size} × {size}.")
    if row % 2:
        return (row - 1) * size + column
    return row * size - column + 1


def cell_position(size: int, value: int) -> tuple[int, int]:
    """Строка и столбец клетки с таким номером."""
    size = check_size(size)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= size * size:
        raise SnakeTableError(f"Номер клетки — от 1 до {size * size}, а не {value!r}.")
    row = (value - 1) // size + 1
    if row % 2:
        column = value - (row - 1) * size
    else:
        column = row * size - value + 1
    return row, column


def completions(size: int, marked: list[int]) -> list[list[int]]:
    """Чем можно дополнить отметки до одной в каждой строке и столбце.

    Возвращаются наборы номеров недостающих клеток, каждый набор
    отсортирован по возрастанию, а сами наборы — по своей сумме.
    """
    size = check_size(size)
    if not isinstance(marked, (list, tuple)):
        raise SnakeTableError(f"Отмеченные клетки задаются списком, а не {marked!r}.")
    places = [cell_position(size, value) for value in marked]
    rows = [row for row, _ in places]
    columns = [column for _, column in places]
    if len(set(rows)) != len(rows) or len(set(columns)) != len(columns):
        raise SnakeTableError(f"Отметки {list(marked)} уже спорят между собой.")
    free_rows = [row for row in range(1, size + 1) if row not in rows]
    free_columns = [column for column in range(1, size + 1) if column not in columns]
    found = []
    for order in itertools.permutations(free_columns):
        group = sorted(
            cell_value(size, row, column) for row, column in zip(free_rows, order)
        )
        found.append(group)
    return sorted(found, key=lambda group: (sum(group), group))


def remaining_sums(size: int, marked: list[int]) -> list[int]:
    """Какие суммы могут дать недостающие клетки — по возрастанию, без повторов."""
    sums = {sum(group) for group in completions(size, marked)}
    return sorted(sums)


def marks_from_permutation(size: int, columns: list[int], keep: int) -> list[int]:
    """Взять первые ``keep`` клеток расстановки — это и будут отметки в условии.

    Обратная параметризация: сначала берётся заведомо правильная
    расстановка целиком, потом часть её прячется. Так условие гарантированно
    выполнимо; подбирать отметки наугад значило бы упираться в жеребьёвки,
    где дополнить нельзя вовсе.
    """
    size = check_size(size)
    if sorted(columns) != list(range(1, size + 1)):
        raise SnakeTableError(f"Расстановка {columns!r} — не перестановка столбцов.")
    if not isinstance(keep, int) or isinstance(keep, bool) or not 1 <= keep < size:
        raise SnakeTableError(f"Показать надо от 1 до {size - 1} отметок, а не {keep!r}.")
    return sorted(cell_value(size, row + 1, columns[row]) for row in range(keep))
