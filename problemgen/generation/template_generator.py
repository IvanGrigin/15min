from __future__ import annotations

import ast
import math
import operator
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from problemgen.catalog.problem_templates import find_templates
from problemgen.core.story_worlds import sample_story_context
from problemgen.russian.agreement import pluralize_ru
import itertools


_OPERATORS: dict[type[ast.AST], Any] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}

_WEEKDAYS_RU = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")


def _count_digit(digit: int, lo: int, hi: int) -> int:
    """Сколько раз цифра появляется при выписывании всех чисел от lo до hi."""
    lo, hi = int(lo), int(hi)
    if lo > hi:
        lo, hi = hi, lo
    if hi - lo > 200_000:
        raise ValueError("Слишком широкий диапазон для count_digit.")
    return "".join(str(n) for n in range(lo, hi + 1)).count(str(int(digit)))


def _count_multiples(k: int, lo: int, hi: int) -> int:
    k, lo, hi = int(k), int(lo), int(hi)
    if lo > hi:
        lo, hi = hi, lo
    return hi // k - (lo - 1) // k


def _num_divisors(n: int) -> int:
    n = abs(int(n))
    if n == 0:
        return 0
    total, i = 0, 1
    while i * i <= n:
        if n % i == 0:
            total += 1 if i * i == n else 2
        i += 1
    return total


def _d02_digits_for_mod3(prefix: int, suffix: int) -> list[int]:
    """Все цифры вместо одной звёздочки, делающие запись кратной трём."""
    fixed_sum = sum(int(char) for char in f"{abs(int(prefix))}{abs(int(suffix))}")
    return [digit for digit in range(10) if (fixed_sum + digit) % 3 == 0]


def _d03_min_factor_sum(product: int, condition: str) -> int:
    """Минимальная сумма пары множителей с явно названным ограничением."""
    product = int(product)
    best: int | None = None
    for first in range(1, math.isqrt(product) + 1):
        if product % first:
            continue
        second = product // first
        valid = {
            "any": True,
            "one_odd": (first % 2) != (second % 2),
            "both_even": first % 2 == 0 and second % 2 == 0,
            "one_square": (first > 1 and math.isqrt(first) ** 2 == first)
            or (second > 1 and math.isqrt(second) ** 2 == second),
        }.get(condition)
        if valid:
            candidate = first + second
            best = candidate if best is None else min(best, candidate)
    if best is None:
        raise ValueError(f"Нет пары множителей для условия {condition!r}.")
    return best


def _d04_min_nozero_factor_sum(product: int) -> int:
    """Минимальная сумма пары делителей без цифры ноль; -1, если пары нет."""
    product = int(product)
    candidates = [
        first + product // first
        for first in range(1, math.isqrt(product) + 1)
        if product % first == 0
        and "0" not in str(first)
        and "0" not in str(product // first)
    ]
    return min(candidates, default=-1)


def _d04_count_bounded_factor_pairs(product: int, lower: int, upper: int) -> int:
    """Число неупорядоченных пар делителей внутри заданных границ."""
    product, lower, upper = int(product), int(lower), int(upper)
    return sum(
        lower <= first <= upper and lower <= product // first <= upper
        for first in range(1, math.isqrt(product) + 1)
        if product % first == 0
    )


def _d05_is_prime(number: int) -> bool:
    number = int(number)
    if number < 2:
        return False
    return all(number % divisor for divisor in range(2, math.isqrt(number) + 1))


def _d05_largest_prime_le(limit: int) -> int:
    for number in range(int(limit), 1, -1):
        if _d05_is_prime(number):
            return number
    raise ValueError("Для границы нет простого числа.")


def _d05_count_primes(limit: int) -> int:
    return sum(_d05_is_prime(number) for number in range(2, int(limit) + 1))


def _d07_pow_mod(base: int, exponent: int, modulus: int) -> int:
    """Остаток степени через модульное возведение без огромного промежуточного числа."""
    return pow(int(base), int(exponent), int(modulus))


def _d08_trailing_zeros_factorial(number: int) -> int:
    """Показатель пятёрки в факториале: двоек в нём заведомо больше."""
    total, number = 0, int(number)
    while number:
        number //= 5
        total += number
    return total


def _d08_trailing_zeros_product(start: int, end: int) -> int:
    """Количество завершающих нулей произведения всех целых от start до end."""
    twos = fives = 0
    for number in range(int(start), int(end) + 1):
        value = number
        while value % 2 == 0:
            twos += 1
            value //= 2
        while value % 5 == 0:
            fives += 1
            value //= 5
    return min(twos, fives)


def _d09_table_parity_answer(columns: int) -> str:
    """Ответ для таблицы: нечётные столбцы вынуждают все числа быть нечётными."""
    return "можно" if int(columns) % 2 == 0 else "нельзя"


def _d09_good_23_values(*numbers: int) -> list[int]:
    """Оставляет числа, чьи простые множители — только 2 и 3."""
    result = []
    for number in (int(value) for value in numbers):
        remainder = number
        for prime in (2, 3):
            while remainder % prime == 0:
                remainder //= prime
        if remainder == 1:
            result.append(number)
    return result


# Белый список функций, разрешённых в answer_formula. Всё вне списка (например
# open) отклоняется — так расширение не открывает произвольный вызов кода.

# --- Helpers added by integrated authoring groups ---

def _first_digit(n: int) -> int:
    """Первая десятичная цифра ненулевого целого числа."""
    return int(str(abs(int(n)))[0])

def _inverse_truncated_twice(first_multiplier: int, second_multiplier: int, result: int) -> int:
    """Восстанавливает единственный прообраз двух операций «умножить и отбросить цифру»."""
    candidates = [
        value for value in range(1, 100_001)
        if ((value * int(first_multiplier)) // 10 * int(second_multiplier)) // 10 == int(result)
    ]
    if len(candidates) != 1:
        raise ValueError("Для операции отбрасывания последней цифры нужен единственный прообраз.")
    return candidates[0]

def _c_count_numbers_with_digit(digit: int, lo: int, hi: int) -> int:
    """Число записей в промежутке, где есть хотя бы одна заданная цифра."""
    digit, lo, hi = int(digit), int(lo), int(hi)
    return sum(str(digit) in str(number) for number in range(min(lo, hi), max(lo, hi) + 1))

def _c_count_numbers_without_digit(digit: int, lo: int, hi: int) -> int:
    """Число записей в промежутке без заданной цифры."""
    digit, lo, hi = int(digit), int(lo), int(hi)
    return sum(str(digit) not in str(number) for number in range(min(lo, hi), max(lo, hi) + 1))

def _c_count_alternating_parity(length: int) -> int:
    """Считает n-значные числа, в которых чётность соседних цифр чередуется."""
    length = int(length)
    if length < 1:
        return 0
    # Начальная цифра: 4 чётных (2,4,6,8) или 5 нечётных; далее в каждой
    # позиции есть ровно 5 цифр противоположной чётности (ноль уже разрешён).
    even_end, odd_end = 4, 5
    for _ in range(length - 1):
        even_end, odd_end = odd_end * 5, even_end * 5
    return even_end + odd_end

def _c_count_digit_sum(length: int, target: int) -> int:
    """Количество length-значных чисел с заданной суммой цифр через малый DP."""
    length, target = int(length), int(target)
    states = {0: 1}
    for position in range(length):
        next_states: dict[int, int] = {}
        lower = 1 if position == 0 else 0
        for subtotal, count in states.items():
            for digit in range(lower, 10):
                if subtotal + digit <= target:
                    next_states[subtotal + digit] = next_states.get(subtotal + digit, 0) + count
        states = next_states
    return states.get(target, 0)

def _c_count_first_digit_gt_last(length: int) -> int:
    """Число length-значных чисел, у которых первая цифра больше последней."""
    length = int(length)
    if length < 2:
        return 0
    return sum(first_digit * 10 ** (length - 2) for first_digit in range(1, 10))

def _e_seq_sum(first: int, multiplier: int, addition: int, count: int) -> int:
    """Сумма ``count`` членов x₁=first, xᵢ₊₁=multiplier*xᵢ+addition.

    Для арифметического случая используется закрытая формула; общий вариант
    нужен авторским задачам E02 и E06 с короткими рекурсивными блоками.
    """
    first, multiplier, addition, count = map(int, (first, multiplier, addition, count))
    if count < 0:
        raise ValueError("Число членов последовательности не может быть отрицательным.")
    if multiplier == 1:
        return count * (2 * first + (count - 1) * addition) // 2
    term, total = first, 0
    for _ in range(count):
        total += term
        term = multiplier * term + addition
    return total

def _fib_term(first: int, second: int, index: int) -> int:
    """Член последовательности x₁=first, x₂=second, xₙ=xₙ₋₁+xₙ₋₂."""
    first, second, index = map(int, (first, second, index))
    if index < 1:
        raise ValueError("Номер члена последовательности должен быть положительным.")
    if index == 1:
        return first
    for _ in range(3, index + 1):
        first, second = second, first + second
    return second

def _perm_multiset(*counts: int) -> int:
    """Число различных перестановок мультимножества заданных кратностей."""
    multiplicities = [int(count) for count in counts]
    if not multiplicities or any(count < 0 for count in multiplicities):
        raise ValueError("Кратности должны быть неотрицательными целыми числами.")
    result = math.factorial(sum(multiplicities))
    for count in multiplicities:
        result //= math.factorial(count)
    return result

def _perm_unrank(order: str, rank: int) -> str:
    """Возвращает перестановку с номером rank (нумерация с 1) в данном порядке букв."""
    symbols, index = list(str(order)), int(rank) - 1
    if len(set(symbols)) != len(symbols) or not 0 <= index < math.factorial(len(symbols)):
        raise ValueError("Недопустимые данные для номера перестановки.")
    result: list[str] = []
    while symbols:
        block = math.factorial(len(symbols) - 1)
        choice, index = divmod(index, block)
        result.append(symbols.pop(choice))
    return "".join(result)

def _weighted_paths_3x3(*values: int) -> int:
    """Считает пути вправо/вверх на поле 3×3 с заданной суммой весов."""
    if len(values) != 10:
        raise ValueError("weighted_paths_3x3 ожидает 9 весов и целевую сумму.")
    *weights, target = (int(value) for value in values)
    grid = [weights[index:index + 3] for index in range(0, 9, 3)]
    sums: dict[tuple[int, int], dict[int, int]] = {(0, 0): {grid[0][0]: 1}}
    for row in range(3):
        for column in range(3):
            if (row, column) == (0, 0):
                continue
            current: dict[int, int] = {}
            for previous in ((row - 1, column), (row, column - 1)):
                for subtotal, count in sums.get(previous, {}).items():
                    total = subtotal + grid[row][column]
                    current[total] = current.get(total, 0) + count
            sums[(row, column)] = current
    return sums[(2, 2)].get(target, 0)

def _count_integer_rectangle_sides(area_minus_perimeter: int) -> int:
    """Число прямоугольников с целыми сторонами a <= b и S - P = c.

    После замены (a - 2)(b - 2) = c + 4 остаётся перебрать только делители;
    порядок сторон не различается.
    """
    target = int(area_minus_perimeter) + 4
    if target <= 0:
        return 0
    return sum(
        1
        for divisor in range(1, math.isqrt(target) + 1)
        if target % divisor == 0 and divisor <= target // divisor
    )

def _grid_square_count(rows: int, columns: int, minimum_side: int = 1) -> int:
    """Считает все осевые квадраты в прямоугольной клетчатой сетке."""
    rows, columns, minimum_side = int(rows), int(columns), int(minimum_side)
    return sum(
        (rows - side + 1) * (columns - side + 1)
        for side in range(minimum_side, min(rows, columns) + 1)
    )

def _grid_internal_partitions(rows: int, cols: int) -> int:
    """Число общих сторон соседних клеток прямоугольника rows × cols."""
    return rows * (cols - 1) + cols * (rows - 1)

def _grid_partitions_with_rectangular_hole(
    rows: int, cols: int, hole_rows: int, hole_cols: int,
) -> int:
    """Перегородки после удаления внутренней прямоугольной дырки по сетке.

    Из числа общих сторон всей решётки вычитаются перегородки внутри дырки
    и по её четырём границам. Предполагается, что дырка не касается края.
    """
    return _grid_internal_partitions(rows, cols) - (2 * hole_rows * hole_cols + hole_rows + hole_cols)

def _weekday_count_in_month(days: int, start_weekday: int, target_weekday: int) -> int:
    """Сколько раз день `target_weekday` встречается в месяце."""
    full_weeks, remainder = divmod(days, 7)
    return full_weeks + int((target_weekday - start_weekday) % 7 < remainder)

def _nth_weekday_date(days: int, start_weekday: int, target_weekday: int, occurrence: int) -> int:
    """Дата заданного по счёту дня недели; стратегия гарантирует её существование."""
    date = 1 + (target_weekday - start_weekday) % 7 + 7 * (occurrence - 1)
    if date > days:
        raise ValueError("В месяце нет указанного по счёту дня недели.")
    return date

def _format_clock(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

def _format_clock_seconds(seconds: int) -> str:
    seconds %= 24 * 60 * 60
    return f"{seconds // 3600:02d}:{(seconds // 60) % 60:02d}:{seconds % 60:02d}"

def _next_distinct_display_seconds(start_seconds: int, occurrence: int) -> int:
    """Момент k-го следующего табло hh:mm:ss с шестью разными цифрами."""
    found = 0
    for moment in range(start_seconds + 1, start_seconds + 2 * 24 * 60 * 60 + 1):
        display = _format_clock_seconds(moment).replace(":", "")
        if len(set(display)) == 6:
            found += 1
            if found == occurrence:
                return moment
    raise ValueError("За двое суток не найдено нужное показание табло.")

def _is_leap_year(year: int) -> bool:
    """Возвращает признак високосного года в григорианском календаре."""
    year = int(year)
    if year < 1:
        raise ValueError("Год должен быть положительным.")
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def _days_in_month(year: int, month: int) -> int:
    """Число дней в месяце григорианского календаря без обращения к datetime."""
    year, month = int(year), int(month)
    if year < 1 or not 1 <= month <= 12:
        raise ValueError("Дата должна содержать положительный год и месяц от 1 до 12.")
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    return 31 if month in {1, 3, 5, 7, 8, 10, 12} else 30

def _weekday_index_of_date(year: int, month: int, day: int) -> int:
    """Индекс дня недели (0 — понедельник) для даты григорианского календаря."""
    year, month, day = int(year), int(month), int(day)
    days_in_current_month = _days_in_month(year, month)
    if not 1 <= day <= days_in_current_month:
        raise ValueError("День месяца выходит за допустимые границы.")
    days_before_year = (year - 1) * 365 + (year - 1) // 4 - (year - 1) // 100 + (year - 1) // 400
    days_before_month = sum(_days_in_month(year, current_month) for current_month in range(1, month))
    # 1 января 1 года по пролептическому григорианскому календарю — понедельник.
    return (days_before_year + days_before_month + day - 1) % 7

def _weekday_of_date(year: int, month: int, day: int) -> str:
    """Название дня недели для реальной даты в григорианском календаре."""
    return _WEEKDAYS_RU[_weekday_index_of_date(year, month, day)]

def _weekday_index(weekday: int | str) -> int:
    """Нормализует номер (0..6) или русское название дня недели."""
    if isinstance(weekday, str):
        try:
            return _WEEKDAYS_RU.index(weekday.lower())
        except ValueError as error:
            raise ValueError(f"Неизвестный день недели: {weekday}.") from error
    if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday < 7:
        raise ValueError("День недели задаётся числом от 0 (понедельник) до 6 (воскресенье).")
    return weekday

def _count_weekday_in_month(year: int, month: int, weekday: int | str) -> int:
    """Сколько раз заданный день недели встречается в указанном месяце."""
    first_weekday = _weekday_index_of_date(year, month, 1)
    weekday = _weekday_index(weekday)
    total_days = _days_in_month(year, month)
    return total_days // 7 + int((weekday - first_weekday) % 7 < total_days % 7)

def _weekday_after_date(year: int, month: int, day: int, days: int) -> str:
    """Название дня недели через целое число дней после указанной даты."""
    return _WEEKDAYS_RU[(_weekday_index_of_date(year, month, day) + int(days)) % 7]

def _nth_weekday_of_month(year: int, month: int, occurrence: int, weekday: int | str) -> int:
    """Дата n-го заданного дня недели в месяце; ошибка, если такого дня нет."""
    occurrence = int(occurrence)
    if occurrence < 1:
        raise ValueError("Номер вхождения дня недели должен быть положительным.")
    weekday = _weekday_index(weekday)
    day = 1 + (weekday - _weekday_index_of_date(year, month, 1)) % 7 + 7 * (occurrence - 1)
    if day > _days_in_month(year, month):
        raise ValueError("В указанном месяце нет такого вхождения дня недели.")
    return day

def _possible_last_weekday_ordinals(month: int, leap_year: int) -> list[int]:
    """Все возможные порядковые номера последнего заданного дня недели месяца.

    При неизвестном дне недели первого числа последний конкретный weekday может
    прийтись на любой из последних семи дней месяца.
    """
    month, leap_year = int(month), int(leap_year)
    year = 2024 if leap_year else 2025
    if leap_year not in {0, 1}:
        raise ValueError("Признак високосности должен быть равен 0 или 1.")
    before_month = sum(_days_in_month(year, current_month) for current_month in range(1, month))
    return list(range(before_month + _days_in_month(year, month) - 6, before_month + _days_in_month(year, month) + 1))

def _format_clock_time(minutes: int) -> str:
    """Нормализует количество минут до 24-часовой записи HH:MM."""
    hours, minutes = divmod(int(minutes) % (24 * 60), 60)
    return f"{hours:02d}:{minutes:02d}"

def _i07_days_until_same_display(gain_per_day: int, loss_per_day: int, initial_difference: int) -> int:
    """Первый день, когда два 12-часовых циферблата покажут одно время."""
    for days in range(1, 721):
        if (int(initial_difference) + days * (int(gain_per_day) + int(loss_per_day))) % 720 == 0:
            return days
    raise ValueError("Показания часов не совпадут за один цикл относительного дрейфа.")

def _i08_nth_all_distinct_time(hour: int, minute: int, second: int, occurrence: int) -> str:
    """Время n-го следующего момента с шестью различными цифрами на табло."""
    start = (int(hour) * 3600 + int(minute) * 60 + int(second)) % 86400
    found = 0
    for elapsed in range(1, 86401):
        current = (start + elapsed) % 86400
        h, rest = divmod(current, 3600)
        m, s = divmod(rest, 60)
        if len(set(f"{h:02d}{m:02d}{s:02d}")) == 6:
            found += 1
            if found == int(occurrence):
                return f"{h:02d}:{m:02d}:{s:02d}"
    raise ValueError("За сутки не найдено требуемое число моментов.")

def _k_reachable_by_gcd(up: int, down: int, difference: int) -> str:
    """Ответ для двух обратимых шагов: достижимость задаёт НОД шагов."""
    return "можно" if int(difference) % math.gcd(int(up), int(down)) == 0 else "нельзя"

def _k_domino_coverable(rows: int, columns: int) -> str:
    """Прямоугольник покрывается домино тогда и только тогда, когда его площадь чётна."""
    return "можно" if int(rows) * int(columns) % 2 == 0 else "нельзя"

def _k_progression_sum_possible(count: int, step: int, total: int) -> str:
    """Проверяет существование положительной АП с заданными суммой и разностью."""
    numerator = 2 * int(total) - int(count) * (int(count) - 1) * int(step)
    denominator = 2 * int(count)
    return "можно" if numerator > 0 and numerator % denominator == 0 else "нельзя"

def _k01_unique_truth_teller() -> str:
    """Перебор фиксированной загадки K01: Аня → «Борис лжёт», Борис → «Вера лжёт», Вера → «Аня и Борис правдивы»."""
    solutions: list[tuple[bool, bool, bool]] = []
    for anya in (False, True):
        for boris in (False, True):
            for vera in (False, True):
                if (anya == (not boris) and boris == (not vera)
                        and vera == (anya and boris)):
                    solutions.append((anya, boris, vera))
    if solutions != [(False, True, False)]:
        raise ValueError("Фиксированная загадка K01 должна иметь единственное решение.")
    return "Борис"

def _k07_first_by_clues() -> str:
    """Перебор фиксированных подсказок K07 о местах Ани, Бориса и Веры."""
    positions = (1, 2, 3)
    solutions = [assignment for assignment in itertools.permutations(positions)
                 if assignment[0] != 1 and assignment[1] < assignment[2] and assignment[2] != 3]
    if solutions != [(3, 1, 2)]:
        raise ValueError("Фиксированная загадка K07 должна иметь единственное решение.")
    return "Борис"

def _k_gcd_reachability_numbers(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Общий делитель > 1 позволяет без цикла строить как достижимые, так и
    # недостижимые цели. Для второй ветви число, не кратное common, точно не
    # кратно и НОД самих шагов.
    common = rng.randint(2, 4)
    factor_limit = min(6, 2 + difficulty // 2)
    up = common * rng.randint(2, factor_limit)
    down = common * rng.randint(2, factor_limit)
    possible = rng.choice((False, True))
    if possible:
        difference = up * rng.randint(2, 5 + difficulty) - down * rng.randint(1, 3 + difficulty // 2)
        while difference <= 0:
            difference += up
    else:
        difference = rng.randint(5, 20 + difficulty * 10)
        while difference % common == 0:
            difference += 1
    return {"up": up, "down": down, "difference": difference}

_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": lambda x: abs(x),
    "min": lambda *xs: min(xs),
    "max": lambda *xs: max(xs),
    "gcd": lambda *xs: math.gcd(*(int(x) for x in xs)),
    "lcm": lambda *xs: math.lcm(*(int(x) for x in xs)),
    "isqrt": lambda n: math.isqrt(int(n)),
    "comb": lambda n, k: math.comb(int(n), int(k)),
    "perm": lambda n, k: math.perm(int(n), int(k)),
    "digit_sum": lambda n: sum(int(c) for c in str(abs(int(n)))),
    "count_digit": _count_digit,
    "count_multiples": _count_multiples,
    "num_divisors": _num_divisors,
    "d02_digits_for_mod3": _d02_digits_for_mod3,
    "d03_min_factor_sum": _d03_min_factor_sum,
    "d04_min_nozero_factor_sum": _d04_min_nozero_factor_sum,
    "d04_count_bounded_factor_pairs": _d04_count_bounded_factor_pairs,
    "d05_largest_prime_le": _d05_largest_prime_le,
    "d05_count_primes": _d05_count_primes,
    "d07_pow_mod": _d07_pow_mod,
    "d08_trailing_zeros_factorial": _d08_trailing_zeros_factorial,
    "d08_trailing_zeros_product": _d08_trailing_zeros_product,
    "d09_table_parity_answer": _d09_table_parity_answer,
    "d09_good_23_values": _d09_good_23_values,
    "weekday_after": lambda start, days: _WEEKDAYS_RU[(int(start) + int(days)) % 7],
    "bigger_label": lambda x, y: "первое" if x > y else ("второе" if y > x else "поровну"),
    'first_digit': _first_digit,
    'inverse_truncated_twice': _inverse_truncated_twice,
    'c_count_numbers_with_digit': _c_count_numbers_with_digit,
    'c_count_numbers_without_digit': _c_count_numbers_without_digit,
    'c_count_alternating_parity': _c_count_alternating_parity,
    'c_count_digit_sum': _c_count_digit_sum,
    'c_count_first_digit_gt_last': _c_count_first_digit_gt_last,
    'e_seq_sum': _e_seq_sum,
    'fib_term': _fib_term,
    'factorial': lambda n: math.factorial(int(n)),
    'perm_multiset': _perm_multiset,
    'perm_unrank': _perm_unrank,
    'weighted_paths_3x3': _weighted_paths_3x3,
    'count_integer_rectangle_sides': _count_integer_rectangle_sides,
    'grid_square_count': _grid_square_count,
    'grid_internal_partitions': _grid_internal_partitions,
    'grid_partitions_with_rectangular_hole': _grid_partitions_with_rectangular_hole,
    'weekday_count_in_month': _weekday_count_in_month,
    'nth_weekday_date': _nth_weekday_date,
    'format_clock': _format_clock,
    'format_clock_seconds': _format_clock_seconds,
    'next_distinct_display_seconds': _next_distinct_display_seconds,
    'weekday_of_date': _weekday_of_date,
    'days_in_month': _days_in_month,
    'count_weekday_in_month': _count_weekday_in_month,
    'weekday_after_date': _weekday_after_date,
    'nth_weekday_of_month': _nth_weekday_of_month,
    'possible_last_weekday_ordinals': _possible_last_weekday_ordinals,
    'format_clock_time': _format_clock_time,
    'i07_days_until_same_display': _i07_days_until_same_display,
    'i08_nth_all_distinct_time': _i08_nth_all_distinct_time,
    'k_reachable_by_gcd': _k_reachable_by_gcd,
    'k_domino_coverable': _k_domino_coverable,
    'k_progression_sum_possible': _k_progression_sum_possible,
    'k01_unique_truth_teller': _k01_unique_truth_teller,
    'k07_first_by_clues': _k07_first_by_clues,
}


@dataclass(frozen=True)
class GeneratedTemplateProblem:
    id: str
    template_id: str
    domain: str
    module: str
    topic: str
    difficulty: int
    problem_text: str
    answer: int | float | str | list[Any]
    variables: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "template_id": self.template_id, "domain": self.domain,
            "module": self.module, "topic": self.topic, "difficulty": self.difficulty,
            "problem_text": self.problem_text, "answer": self.answer, "variables": self.variables,
        }


# Реестр алгоритмов подбора чисел. Каждый шаблон в JSON ссылается на стратегию
# по имени через поле number_strategy; сами алгоритмы живут здесь как маленькие
# именованные функции. Это единственное место, куда добавляется Python-код при
# росте каталога шаблонов — новые сюжеты того же математического типа не требуют
# правок и добавляются только в JSON. См. Docs/PROBLEM_TEMPLATES.md.
_NumberBuilder = Callable[[int, random.Random], dict[str, int]]
_NUMBER_STRATEGIES: dict[str, _NumberBuilder] = {}


def _number_strategy(name: str) -> Callable[[_NumberBuilder], _NumberBuilder]:
    def register(builder: _NumberBuilder) -> _NumberBuilder:
        if name in _NUMBER_STRATEGIES:
            raise ValueError(f"Стратегия чисел '{name}' зарегистрирована дважды.")
        _NUMBER_STRATEGIES[name] = builder
        return builder
    return register


def _difficulty_range(difficulty: int, low: int, high: int) -> tuple[int, int]:
    ceiling = low + max(1, round((high - low) * difficulty / 10))
    return low, min(high, ceiling)


@_number_strategy("joint_work_two")
def _joint_work_two(difficulty: int, rng: random.Random) -> dict[str, int]:
    rate_low, rate_high = _difficulty_range(difficulty, 2, 12)
    t1, t2 = rng.randint(1, 4), rng.randint(1, 4)
    return {"time_1": t1, "time_2": t2, "amount_1": rng.randint(rate_low, rate_high) * t1, "amount_2": rng.randint(rate_low, rate_high) * t2, "duration": rng.randint(1, min(5, difficulty // 2 + 1))}


@_number_strategy("joint_work_three")
def _joint_work_three(difficulty: int, rng: random.Random) -> dict[str, int]:
    time = rng.randint(1, 4)
    low, high = _difficulty_range(difficulty, 5, 12)
    return {"time_1": time, "amount_1": rng.randint(low, high) * time, "amount_2": rng.randint(low, high) * time, "amount_3": rng.randint(low, high) * time, "duration": rng.randint(1, min(5, difficulty // 2 + 1))}


@_number_strategy("age_friends")
def _age_friends(difficulty: int, rng: random.Random) -> dict[str, int]:
    friends = rng.randint(2, min(8, difficulty + 2))
    years = rng.randint(1, min(10, difficulty + 1))
    current = rng.randint(4, 12) * friends
    return {"current_total": current, "years_later": years, "future_total": current + friends * years}


@_number_strategy("heads_and_legs")
def _heads_and_legs(difficulty: int, rng: random.Random) -> dict[str, int]:
    # ducks >= 2 гарантирует heads >= 3 и legs >= 8 — нижние границы constraints.
    rabbits = rng.randint(1, max(2, difficulty + 1))
    ducks = rng.randint(2, max(3, difficulty + 2))
    return {"heads": rabbits + ducks, "legs": rabbits * 4 + ducks * 2}


@_number_strategy("ratio_sum")
def _ratio_sum(difficulty: int, rng: random.Random) -> dict[str, int]:
    # ratio_a строго больше ratio_b: отношение никогда не вырождается в 1:1, а в
    # условии можно однозначно спросить про «большую часть» без падежей имён.
    ratio_a = rng.randint(2, 6)
    ratio_b = rng.randint(1, ratio_a - 1)
    multiplier = rng.randint(2, difficulty + 5)
    return {"ratio_a": ratio_a, "ratio_b": ratio_b, "total": (ratio_a + ratio_b) * multiplier}


@_number_strategy("round_robin")
def _round_robin(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"players": rng.randint(3, min(30, difficulty * 3 + 3))}


@_number_strategy("paint_cube")
def _paint_cube(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"base_side": rng.randint(1, min(20, difficulty + 3)), "base_paint": rng.randint(2, difficulty * 10 + 10), "scale": rng.randint(2, min(8, difficulty // 2 + 2))}


@_number_strategy("equal_payment")
def _equal_payment(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Множители подрезаны так, чтобы значения не выходили за constraints:
    # total <= 20000 (×200 → ≤100), loan <= 30000 (×100 → ≤300), paid_2 <= 20000.
    total = rng.randint(5, min(100, difficulty * 25 + 25)) * 200
    loan = rng.randint(5, min(300, difficulty * 30 + 30)) * 100
    paid_2 = rng.randint(100, min(20000, total // 2 + loan // 2 - 1))
    return {"total": total, "loan": loan, "paid_2": paid_2}


@_number_strategy("movement_together")
def _movement_together(difficulty: int, rng: random.Random) -> dict[str, int]:
    top = min(30, difficulty * 3 + 3)
    return {"speed_1": rng.randint(1, top), "speed_2": rng.randint(1, top), "duration": rng.randint(1, min(8, difficulty + 1))}


@_number_strategy("age_joining_group")
def _age_joining_group(difficulty: int, rng: random.Random) -> dict[str, int]:
    friends = rng.randint(2, min(8, difficulty + 2))
    years = rng.randint(2, min(10, difficulty + 3))
    extra_people = rng.randint(1, 3)
    current_total = rng.randint(5, 14) * friends
    extra_current_total = rng.randint(4, 12) * extra_people
    future_total = current_total + friends * years + extra_current_total + extra_people * years
    return {
        "current_total": current_total,
        "years_later": years,
        "extra_people": extra_people,
        "extra_current_total": extra_current_total,
        "future_total": future_total,
    }


@_number_strategy("ratio_transfer")
def _ratio_transfer(difficulty: int, rng: random.Random) -> dict[str, int]:
    ratio_a = rng.randint(3, 7)
    ratio_b = rng.randint(1, ratio_a - 2)
    # multiplier >= 4 при сумме долей >= 4 держит total = (a+b)*mult не ниже 15.
    multiplier = rng.randint(4, difficulty + 7)
    transfer = rng.randint(1, max(1, multiplier * (ratio_a - ratio_b) // 2 - 1))
    total = (ratio_a + ratio_b) * multiplier
    final_difference = (ratio_a - ratio_b) * multiplier - 2 * transfer
    return {
        "ratio_a": ratio_a,
        "ratio_b": ratio_b,
        "total": total,
        "transfer": transfer,
        "final_difference": final_difference,
    }


@_number_strategy("heads_and_legs_removed")
def _heads_and_legs_removed(difficulty: int, rng: random.Random) -> dict[str, int]:
    rabbits = rng.randint(3, max(4, difficulty + 3))
    ducks = rng.randint(2, max(3, difficulty + 4))
    removed_rabbits = rng.randint(1, rabbits - 1)
    heads_after = rabbits + ducks - removed_rabbits
    legs_after = (rabbits - removed_rabbits) * 4 + ducks * 2
    return {"heads_after": heads_after, "legs_after": legs_after, "removed_rabbits": removed_rabbits}


@_number_strategy("joint_work_delay")
def _joint_work_delay(difficulty: int, rng: random.Random) -> dict[str, int]:
    rate_low, rate_high = _difficulty_range(difficulty, 3, 14)
    rate_1 = rng.randint(rate_low, rate_high)
    rate_2 = rng.randint(rate_low, rate_high)
    duration = rng.randint(3, min(9, difficulty + 4))
    delay = rng.randint(1, duration - 1)
    return {
        "rate_1": rate_1,
        "rate_2": rate_2,
        "duration": duration,
        "delay": delay,
        "total": rate_1 * duration + rate_2 * (duration - delay),
    }


@_number_strategy("round_robin_missing")
def _round_robin_missing(difficulty: int, rng: random.Random) -> dict[str, int]:
    players = rng.randint(5, min(34, difficulty * 3 + 7))
    absent_players = rng.randint(1, min(4, players - 3))
    return {
        "players": players,
        "absent_players": absent_players,
        "active_players": players - absent_players,
    }


@_number_strategy("paint_cube_unpainted")
def _paint_cube_unpainted(difficulty: int, rng: random.Random) -> dict[str, int]:
    base_paint = rng.randint(1, difficulty * 3 + 3) * 6
    scale = rng.randint(2, min(8, difficulty // 2 + 3))
    unpainted_faces = rng.randint(1, 2)
    return {"base_paint": base_paint, "scale": scale, "unpainted_faces": unpainted_faces}


@_number_strategy("movement_two_stage")
def _movement_two_stage(difficulty: int, rng: random.Random) -> dict[str, int]:
    top = min(40, difficulty * 4 + 8)
    return {
        "speed_1": rng.randint(3, top),
        "time_1": rng.randint(1, min(5, difficulty + 1)),
        "speed_2": rng.randint(3, top),
        "time_2": rng.randint(1, min(5, difficulty + 1)),
        "rest_time": rng.randint(1, 3),
    }


@_number_strategy("opposite_motion_delay")
def _opposite_motion_delay(difficulty: int, rng: random.Random) -> dict[str, int]:
    speed_1 = rng.randint(4, min(50, difficulty * 5 + 10))
    speed_2 = rng.randint(4, min(50, difficulty * 5 + 10))
    delay = rng.randint(1, min(4, difficulty))
    together_time = rng.randint(1, min(6, difficulty + 1))
    return {
        "speed_1": speed_1,
        "speed_2": speed_2,
        "delay": delay,
        "distance": speed_1 * delay + (speed_1 + speed_2) * together_time,
    }


@_number_strategy("factor_shortcut_compare")
def _factor_shortcut_compare(difficulty: int, rng: random.Random) -> dict[str, int]:
    n = rng.randint(20, difficulty * 60 + 80)
    shift = rng.randint(2, 9)
    return {"n": n, "shift": shift}


@_number_strategy("price_system_two_receipts")
def _price_system_two_receipts(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Цена подрезана до 290: при counts <= 8 максимум total = 8*290 + 8*290 = 4640,
    # что укладывается в самую тесную границу total <= 5000 у части шаблонов.
    price_a = rng.randint(2, min(29, difficulty * 8 + 12)) * 10
    price_b = rng.randint(2, min(29, difficulty * 8 + 12)) * 10
    count_a_1 = rng.randint(1, min(8, difficulty + 3))
    count_b_1 = rng.randint(1, min(8, difficulty + 3))
    count_a_2 = rng.randint(1, min(8, difficulty + 3))
    count_b_2 = rng.randint(1, min(8, difficulty + 3))
    while count_a_1 * count_b_2 == count_a_2 * count_b_1:
        count_a_2 = rng.randint(1, min(8, difficulty + 3))
        count_b_2 = rng.randint(1, min(8, difficulty + 3))
    return {
        "count_a_1": count_a_1,
        "count_b_1": count_b_1,
        "count_a_2": count_a_2,
        "count_b_2": count_b_2,
        "total_1": count_a_1 * price_a + count_b_1 * price_b,
        "total_2": count_a_2 * price_a + count_b_2 * price_b,
        "answer_price_a": price_a,
    }


# --- стратегии для типов, разблокированных расширенным движком (needs_extension) ---

@_number_strategy("digit_count_range")
def _digit_count_range(difficulty: int, rng: random.Random) -> dict[str, int]:
    digit = rng.randint(1, 9)
    lo = rng.randint(1, 50)
    hi = lo + rng.randint(40, 60 + difficulty * 90)
    return {"digit": digit, "lo": lo, "hi": hi}


@_number_strategy("gcd_pair")
def _gcd_pair(difficulty: int, rng: random.Random) -> dict[str, int]:
    common = rng.randint(2, 6 + difficulty)
    return {"a": common * rng.randint(2, 9), "b": common * rng.randint(2, 9)}


@_number_strategy("weekday_after")
def _weekday_after_numbers(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"days": rng.randint(3, 30 + difficulty * 40)}


@_number_strategy("two_products")
def _two_products(difficulty: int, rng: random.Random) -> dict[str, int]:
    base = rng.randint(10, 20 + difficulty * 10)
    return {
        "a": base + rng.randint(1, 9), "b": base + rng.randint(1, 9),
        "c": base + rng.randint(1, 9), "d": base + rng.randint(1, 9),
    }


@_number_strategy("compare_triple_products")
def _compare_triple_products(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Классический приём: два произведения с общим средним множителем и крайними,
    # различающимися на ±delta. Разность мала и вычисляется точно.
    mid = rng.randint(2, 9) * (10 ** (difficulty % 3 + 1)) + rng.randint(0, 9)
    n = rng.randint(1000, 1000 + difficulty * 900)
    m = rng.randint(1000, 1000 + difficulty * 900)
    delta = rng.randint(1, 3)
    return {"a": n, "mid": mid, "b": m, "c": n - delta, "d": m + delta}


# --- авторские стратегии группы D: теория чисел ---

@_number_strategy("d01_multiples_interval")
def _d01_multiples_interval(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Промежуток с достаточным числом кратных для включающих и строгих границ."""
    left = rng.randint(5, 50 + difficulty * 90)
    right = left + rng.randint(40, 120 + difficulty * 160)
    mod_a = rng.randint(2, min(18, difficulty + 8))
    mod_b = rng.randint(2, min(15, difficulty + 7))
    while mod_b == mod_a:
        mod_b = rng.randint(2, min(15, difficulty + 7))
    return {"left": left, "right": right, "mod_a": mod_a, "mod_b": mod_b}


@_number_strategy("d02_missing_digit")
def _d02_missing_digit(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Части записи числа вокруг одной пропущенной цифры без ведущих нулей."""
    prefix = rng.randint(10, 99_999 + difficulty * 90_000)
    suffix = rng.randint(10, 99)
    return {"prefix": prefix, "suffix": suffix}


@_number_strategy("d03_factor_pair")
def _d03_factor_pair(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Составное число с допустимыми парами для трёх ограничений D03."""
    odd = rng.randrange(3, 11 + difficulty * 6, 2)
    even_1 = 2 * rng.randint(2, 8 + difficulty * 2)
    even_2 = 2 * rng.randint(2, 8 + difficulty * 2)
    return {"product": odd * even_1 * even_2}


@_number_strategy("d04_constrained_factorization")
def _d04_constrained_factorization(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Произведение двух чисел без нулей и безопасные границы для пар."""
    limit = 30 + difficulty * 90
    first = rng.randint(2, limit)
    while "0" in str(first):
        first = rng.randint(2, limit)
    second = rng.randint(2, limit)
    while "0" in str(second):
        second = rng.randint(2, limit)
    return {"product": first * second, "lower": 2, "upper": max(first, second)}


@_number_strategy("d05_prime_parameter")
def _d05_prime_parameter(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Пределы, в которых заведомо есть несколько простых чисел."""
    return {"limit": rng.randint(20, 90 + difficulty * 90)}


@_number_strategy("d06_gcd_lcm_periods")
def _d06_gcd_lcm_periods(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Два периода с нетривиальным общим делителем и разумным НОК."""
    common = rng.randint(2, 4 + difficulty)
    first_multiplier = rng.randint(2, 5 + difficulty)
    second_multiplier = rng.randint(2, 5 + difficulty)
    while second_multiplier == first_multiplier:
        second_multiplier = rng.randint(2, 5 + difficulty)
    return {"first": common * first_multiplier, "second": common * second_multiplier}


@_number_strategy("d07_modular_power_cycle")
def _d07_modular_power_cycle(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Большой показатель, для которого ответ требует заметить цикл остатков."""
    return {
        "base": rng.randint(2, 20 + difficulty * 12),
        "exponent": rng.randint(25, 600 + difficulty * 1400),
        "modulus": rng.randint(3, min(31, difficulty * 3 + 8)),
    }


@_number_strategy("d08_trailing_zeros")
def _d08_trailing_zeros(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Интервал и факториал достаточной длины, чтобы нули были нетривиальны."""
    start = rng.randint(2, 10 + difficulty * 12)
    end = start + rng.randint(10, 35 + difficulty * 22)
    return {"start": start, "end": end, "factorial_n": rng.randint(25, 90 + difficulty * 85)}


@_number_strategy("d09_parity_construction")
def _d09_parity_construction(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Размеры таблицы и смешанный список чисел с контролируемыми множителями."""
    rows = rng.randint(2, 3 + difficulty)
    columns = rng.randint(3, 4 + difficulty)
    good_1 = 2 ** rng.randint(1, 4) * 3 ** rng.randint(0, 3)
    good_2 = 2 ** rng.randint(0, 4) * 3 ** rng.randint(1, 3)
    bad_1 = good_1 * 5
    bad_2 = good_2 * 7
    return {
        "rows": rows,
        "columns": columns,
        "candidate_1": good_1,
        "candidate_2": bad_1,
        "candidate_3": good_2,
        "candidate_4": bad_2,
    }



# --- Strategies added by integrated authoring groups ---

@_number_strategy("arithmetic_a01_expression")
def _arithmetic_a01_expression(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"a": rng.randint(2, 10 + difficulty * 4), "b": rng.randint(2, 10 + difficulty * 4), "c": rng.randint(2, 6 + difficulty)}

@_number_strategy("arithmetic_a02_nested_expression")
def _arithmetic_a02_nested_expression(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Генерация от ответа: выбираем частное quotient и делитель divisor, затем
    # подбираем c так, чтобы (a - b) * k + c = divisor * quotient делилось нацело.
    # Ключевое: a - b ДОЛЖНО равняться difference (раньше a,b брались независимо и
    # деление получалось неточным), поэтому a = b + difference.
    difference = rng.randint(2, 8 + difficulty)
    k, divisor = rng.randint(2, 8), rng.randint(2, 8)
    quotient = rng.randint((difference * k + divisor - 1) // divisor + 2, 300)
    b = rng.randint(2, 15 + difficulty)
    a = b + difference
    c = divisor * quotient - difference * k
    assert (a - b) * k + c == divisor * quotient  # обратная проверка: деление точное
    return {"a": a, "b": b, "k": k, "c": c, "d": divisor}

@_number_strategy("arithmetic_a03_common_factor")
def _arithmetic_a03_common_factor(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"factor": rng.randint(10, 30 + difficulty * 10), "left": rng.randint(2, 20 + difficulty * 3), "right": rng.randint(2, 20 + difficulty * 3)}

@_number_strategy("arithmetic_a05_exact_quotient")
def _arithmetic_a05_exact_quotient(difficulty: int, rng: random.Random) -> dict[str, int]:
    divisor = rng.randint(12, 99 + difficulty * 10)
    quotient = rng.randint(1_000, 10_000 + difficulty * 9_000)
    return {"dividend": divisor * quotient, "divisor": divisor}

@_number_strategy("arithmetic_a06_first_digit")
def _arithmetic_a06_first_digit(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"a": rng.randint(100, 900 + difficulty * 400), "b": rng.randint(100, 900 + difficulty * 400)}

@_number_strategy("arithmetic_a07_integer_bound")
def _arithmetic_a07_integer_bound(difficulty: int, rng: random.Random) -> dict[str, int]:
    difference, multiplier, divisor = rng.randint(2, 15 + difficulty), rng.randint(2, 10 + difficulty), rng.randint(2, 9)
    quotient = rng.randint((difference * multiplier + divisor - 1) // divisor + 2, 300)
    return {"a": difference + rng.randint(2, 15 + difficulty), "b": rng.randint(2, 15 + difficulty), "c": multiplier, "d": divisor, "e": divisor * quotient - difference * multiplier}

@_number_strategy("arithmetic_a08_truncated_digits")
def _arithmetic_a08_truncated_digits(difficulty: int, rng: random.Random) -> dict[str, int]:
    initial = rng.randint(10, 1_000 + difficulty * 500)
    # 20, затем 5: обе операции отбрасывают нулевую последнюю цифру, но обратный
    # образ строго единственный и helper всё равно проверяет это перебором.
    return {"first_multiplier": 20, "second_multiplier": 5, "result": initial}

@_number_strategy("b_linear_equation_chain")
def _b_linear_equation_chain(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Build both B01 equation forms from a chosen integral root x."""
    x = rng.randint(2, min(30, difficulty * 3 + 6))
    divisor = rng.randint(2, min(18, difficulty * 2 + 4))
    quotient = rng.randint(divisor + 1, min(40, divisor + difficulty * 5 + 8))
    a = rng.randint(100, min(2_000, difficulty * 220 + 300))
    d = rng.randint(2, min(15, difficulty + 4))
    c = x * quotient
    e = a + divisor * d
    offset = rng.randint(10, min(160, difficulty * 20 + 30))
    b = x * divisor + offset
    subtractor = rng.randint(20, min(300, difficulty * 35 + 40))
    a_nested = rng.randint(offset * d + subtractor + 100, min(8_000, offset * d + subtractor + difficulty * 500 + 1_000))
    target = a_nested - offset * d - subtractor
    return {
        "x": x,
        "a": a,
        "b_div": quotient + divisor,
        "c": c,
        "d": d,
        "e": e,
        "a_nested": a_nested,
        "b_nested": b,
        "c_nested": divisor,
        "d_nested": d,
        "subtractor": subtractor,
        "target": target,
    }

@_number_strategy("b08_concentration")
def _b08_concentration(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Choose percentages that preserve an integral dry mass and final mass."""
    water_before, water_after = rng.choice(((80, 60), (90, 80), (95, 90), (99, 98)))
    dry_mass = 2 * rng.randint(1, min(20, difficulty * 2 + 4))
    return {
        "initial_mass": dry_mass * 100 // (100 - water_before),
        "water_before": water_before,
        "water_after": water_after,
    }

@_number_strategy("b09_direct_proportion")
def _b09_direct_proportion(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Select a whole-unit rate so both proportional costs are integral."""
    unit_cost = rng.randint(5, min(80, difficulty * 8 + 16))
    known_amount = rng.randint(2, min(20, difficulty * 2 + 4))
    target_amount = rng.randint(2, min(30, difficulty * 3 + 6))
    return {
        "known_amount": known_amount,
        "known_cost": known_amount * unit_cost,
        "target_amount": target_amount,
    }

@_number_strategy("b10_equal_transfer")
def _b10_equal_transfer(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Choose an even target difference created by one transfer from equal sums."""
    transfer = rng.randint(1, min(100, difficulty * 12 + 12))
    return {"target_difference": 2 * transfer}

@_number_strategy("c01_even_interval")
def _c01_even_interval(difficulty: int, rng: random.Random) -> dict[str, int]:
    left = rng.randint(1, 100 + difficulty * 100)
    right = left + rng.randint(20, 200 + difficulty * 120)
    return {"left": left, "right": right}

@_number_strategy("c02_contains_digit")
def _c02_contains_digit(difficulty: int, rng: random.Random) -> dict[str, int]:
    left = rng.randint(100, 400 + difficulty * 150)
    return {"left": left, "right": left + rng.randint(120, 500 + difficulty * 150), "digit": rng.randint(1, 9)}

@_number_strategy("c03_avoids_digit")
def _c03_avoids_digit(difficulty: int, rng: random.Random) -> dict[str, int]:
    left = rng.randint(100, 400 + difficulty * 150)
    return {"left": left, "right": left + rng.randint(120, 500 + difficulty * 150), "digit": rng.randint(1, 9)}

@_number_strategy("c05_alternating_parity")
def _c05_alternating_parity(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"length": rng.randint(3, min(6, difficulty + 2))}

@_number_strategy("c06_last_digit_power")
def _c06_last_digit_power(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"base": rng.randint(2, 19 + difficulty * 7), "exponent": rng.randint(5, min(64, 8 + difficulty * 6))}

@_number_strategy("c07_digit_sum_count")
def _c07_digit_sum_count(difficulty: int, rng: random.Random) -> dict[str, int]:
    length = rng.randint(3, min(6, difficulty + 2))
    return {"length": length, "target_sum": rng.randint(4, 9 * length - 4)}

@_number_strategy("c08_first_digit_gt_last")
def _c08_first_digit_gt_last(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"length": rng.randint(3, min(7, difficulty + 2))}

@_number_strategy("c09_distinct_digit_numbers")
def _c09_distinct_digit_numbers(difficulty: int, rng: random.Random) -> dict[str, int]:
    available = rng.randint(5, 9)
    return {"available": available, "length": rng.randint(2, min(5, available))}

@_number_strategy("c10_missing_addend_digit")
def _c10_missing_addend_digit(difficulty: int, rng: random.Random) -> dict[str, int]:
    missing = rng.randint(0, 9)
    addend = rng.randint(12, 90 + difficulty * 20)
    return {"addend": addend, "total": addend + missing}

@_number_strategy("c11_same_suffix_numbers")
def _c11_same_suffix_numbers(difficulty: int, rng: random.Random) -> dict[str, int]:
    first, second, third = 1, 3, 5
    suffix = rng.randint(0, 99)
    return {
        "first": first,
        "second": second,
        "third": third,
        "suffix": suffix,
        "total": (first + second + third) * 100 + 3 * suffix,
    }

@_number_strategy("c12_consecutive_digit_block")
def _c12_consecutive_digit_block(difficulty: int, rng: random.Random) -> dict[str, int]:
    count = rng.randint(40, 120 + difficulty * 20)
    four_digit_count = rng.randint(1, count - 1)
    return {"count": count, "total_digits": 3 * count + four_digit_count}

@_number_strategy("e_ap_sum")
def _e_ap_sum(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Параметры невырожденной арифметической прогрессии для E01."""
    a = rng.randint(2, 12 + difficulty * 8)
    d = rng.randint(1, 2 + difficulty)
    n = rng.randint(4, min(24, 5 + difficulty * 2))
    return {
        "a": a,
        "d": d,
        "n": n,
        "next_term": a + d,
        "last": a + (n - 1) * d,
    }

@_number_strategy("e_alternating_block_sum")
def _e_alternating_block_sum(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Пары с одинаковым сокращением и нечётная знакочередующаяся сумма E02."""
    a = rng.randint(2, 15 + difficulty * 8)
    pair_count = rng.randint(3, min(24, 4 + difficulty * 2))
    return {
        "a": a,
        "b": a + 1,
        "c": a + 3,
        "d": a + 4,
        "pair_count": pair_count,
        "last": a + 3 * (pair_count - 1) + 1,
        "odd_last": 4 * pair_count + 1,
    }

@_number_strategy("e_double_minus_pattern")
def _e_double_minus_pattern(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Последовательность с чередованием операций «умножить на 2» и «вычесть»."""
    a = rng.randint(8, 20 + difficulty * 8)
    step = rng.randint(1, 2 + difficulty)
    terms = [a]
    for index in range(1, 9):
        terms.append(terms[-1] * 2 if index % 2 else terms[-1] - step)
    return {
        "a1": terms[0], "a2": terms[1], "a3": terms[2],
        "a4": terms[3], "a5": terms[4], "a6": terms[5],
        "next1": terms[6], "next2": terms[7], "next3": terms[8],
        "step": step,
    }

@_number_strategy("e_affine_pattern")
def _e_affine_pattern(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Короткая последовательность xₙ₊₁=kxₙ+c для E03."""
    a = rng.randint(1, 8 + difficulty * 3)
    k = rng.randint(2, min(4, 1 + difficulty // 3 + 2))
    c = rng.randint(1, 2 + difficulty)
    n = rng.randint(3, min(8, 3 + difficulty // 2))
    return {"a": a, "k": k, "c": c, "n": n, "a2": k * a + c, "a3": k * (k * a + c) + c}

@_number_strategy("e_fibonacci_type")
def _e_fibonacci_type(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Небольшие параметры для последовательностей типа Фибоначчи E04."""
    endpoint = rng.randint(7, min(18, 8 + difficulty))
    start_point = rng.randint(1, endpoint - 3)
    return {
        "a": rng.randint(1, 4 + difficulty),
        "b": rng.randint(1, 4 + difficulty),
        "term_index": rng.randint(5, min(15, 5 + difficulty)),
        "k": start_point,
        "n": endpoint,
    }

@_number_strategy("e_collatz_threshold")
def _e_collatz_threshold(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Короткая, заранее завершённая траектория правила 3n+1 для E05."""
    threshold = rng.randint(5, 10 + difficulty * 2)
    for _ in range(200):
        start = rng.randint(threshold + 5, min(5000, 100 + difficulty * 500))
        value, steps, saw_odd = start, 0, False
        while value >= threshold and steps < 200:
            saw_odd |= value % 2 == 1
            value = value // 2 if value % 2 == 0 else 3 * value + 1
            steps += 1
        if value < threshold and steps >= 3 and saw_odd:
            return {"start": start, "threshold": threshold, "steps": steps}
    raise RuntimeError("Не удалось подобрать короткую траекторию для E05.")

@_number_strategy("e_cyclic_operations")
def _e_cyclic_operations(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Чередование двух явно указанных операций с заранее вычисленным итогом."""
    start = rng.randint(2, 10 + difficulty * 5)
    addition = rng.randint(1, 3 + difficulty)
    pairs = rng.randint(2, min(8, 2 + difficulty // 2))
    value = start
    for _ in range(pairs):
        value = (value + addition) * 2
    return {"start": start, "addition": addition, "steps": 2 * pairs, "result": value}

@_number_strategy("e_recursive_total_growth")
def _e_recursive_total_growth(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Параметры короткой рекуррентной суммы и суммы АП для E06."""
    return {
        "initial": rng.randint(1, 5 + difficulty),
        "multiplier": rng.randint(2, 3),
        "addition": rng.randint(1, 3 + difficulty),
        "n": rng.randint(3, min(8, 3 + difficulty // 2)),
        "a": rng.randint(2, 10 + difficulty * 5),
        "d": rng.randint(1, 2 + difficulty),
        "days": rng.randint(4, min(24, 5 + difficulty * 2)),
    }

@_number_strategy("comb_permutations_distinct")
def _comb_permutations_distinct(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"n": rng.randint(4, min(8, difficulty + 4))}

@_number_strategy("comb_permutations_repeated")
def _comb_permutations_repeated(difficulty: int, rng: random.Random) -> dict[str, int]:
    first_count = rng.randint(2, 4)
    second_count = rng.randint(1, min(3, difficulty // 3 + 1))
    return {"first_count": first_count, "second_count": second_count}

@_number_strategy("comb_bounded_words")
def _comb_bounded_words(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"alphabet_size": rng.randint(2, min(5, difficulty + 2)), "max_length": rng.randint(2, min(6, difficulty + 2))}

@_number_strategy("comb_unknown_alphabet")
def _comb_unknown_alphabet(difficulty: int, rng: random.Random) -> dict[str, int | str]:
    return {"order": "КЛЕН", "target_rank": rng.randint(2, 24)}

@_number_strategy("comb_team_selection")
def _comb_team_selection(difficulty: int, rng: random.Random) -> dict[str, int]:
    members = rng.randint(6, min(14, difficulty + 7))
    return {"members": members, "team_size": rng.randint(2, min(5, members - 1))}

@_number_strategy("comb_round_robin_pairs")
def _comb_round_robin_pairs(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"players": rng.randint(3, min(30, difficulty * 3 + 3))}

@_number_strategy("comb_elimination_matches")
def _comb_elimination_matches(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"players": 2 ** rng.randint(2, min(5, difficulty // 2 + 2))}

@_number_strategy("comb_lattice_paths")
def _comb_lattice_paths(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"right_steps": rng.randint(2, min(8, difficulty + 2)), "up_steps": rng.randint(2, min(8, difficulty + 2))}

@_number_strategy("comb_weighted_grid_paths")
def _comb_weighted_grid_paths(difficulty: int, rng: random.Random) -> dict[str, int]:
    weights = [rng.randint(1, min(7, difficulty + 2)) for _ in range(9)]
    row, column, target = 0, 0, weights[0]
    for move in rng.sample(["R", "R", "U", "U"], 4):
        if move == "R":
            column += 1
        else:
            row += 1
        target += weights[row * 3 + column]
    return {**{f"w{index + 1}": value for index, value in enumerate(weights)}, "target": target}

@_number_strategy("comb_nonattacking_rooks")
def _comb_nonattacking_rooks(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"board_size": rng.randint(3, min(8, difficulty + 2))}

@_number_strategy("comb_pigeonhole_target")
def _comb_pigeonhole_target(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"non_target": rng.randint(2, min(30, difficulty * 3 + 3))}

@_number_strategy("geometry_g01_square_perimeter")
def _geometry_g01_square_perimeter(difficulty: int, rng: random.Random) -> dict[str, int]:
    side = rng.randint(2, 8 + difficulty * 4)
    return {"perimeter": 4 * side}

@_number_strategy("geometry_g02_rectangle_area")
def _geometry_g02_rectangle_area(difficulty: int, rng: random.Random) -> dict[str, int]:
    side_a = rng.randint(2, 7 + difficulty * 2)
    side_b = rng.randint(2, 7 + difficulty * 3)
    return {"area": side_a * side_b, "side_a": side_a}

@_number_strategy("geometry_g03_tiled_square")
def _geometry_g03_tiled_square(difficulty: int, rng: random.Random) -> dict[str, int]:
    small_side = rng.randint(1, 4 + difficulty)
    tiles_per_side = rng.randint(2, min(10, difficulty + 3))
    return {"small_area": small_side * small_side, "tiles_per_side": tiles_per_side}

@_number_strategy("geometry_g04_cut_perimeter")
def _geometry_g04_cut_perimeter(difficulty: int, rng: random.Random) -> dict[str, int]:
    width = rng.randint(3, 8 + difficulty * 3)
    height = rng.randint(2, 7 + difficulty * 2)
    return {"perimeter": 2 * (width + height), "perimeters_sum": 2 * (width + height) + 2 * height}

@_number_strategy("geometry_g05_integer_rectangles")
def _geometry_g05_integer_rectangles(difficulty: int, rng: random.Random) -> dict[str, int]:
    # c + 4 = (a - 2)(b - 2); произведение с несколькими делителями делает
    # вопрос о числе прямоугольников содержательнее одного примера.
    factors = rng.choice(((2, 3), (2, 4), (2, 6), (3, 4), (3, 6), (4, 6), (5, 6)))
    scale = rng.randint(1, min(4, difficulty // 2 + 1))
    target = factors[0] * factors[1] * scale
    return {"area_minus_perimeter": target - 4}

@_number_strategy("geometry_g06_area_scaling")
def _geometry_g06_area_scaling(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"scale": rng.randint(2, min(10, difficulty + 2))}

@_number_strategy("geometry_g07_area_unit_conversion")
def _geometry_g07_area_unit_conversion(difficulty: int, rng: random.Random) -> dict[str, int]:
    density = rng.randint(1, 9 + difficulty)
    area_cm2 = rng.randint(2, 30 + difficulty * 15) * 100
    return {
        "area_cm2": area_cm2,
        "mass": area_cm2 * density,
        "area_dm2": rng.randint(1, 4 + difficulty),
    }

@_number_strategy("geometry_g08_grid_squares")
def _geometry_g08_grid_squares(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "rows": rng.randint(2, min(12, difficulty + 4)),
        "columns": rng.randint(2, min(14, difficulty + 5)),
    }

@_number_strategy("geometry_g09_collinear_segments")
def _geometry_g09_collinear_segments(difficulty: int, rng: random.Random) -> dict[str, int]:
    ab = rng.randint(1, 8 + difficulty * 2)
    return {"ab": ab, "ce": ab + rng.randint(1, 8 + difficulty * 2)}

@_number_strategy("geometry_g10_alternating_gaps")
def _geometry_g10_alternating_gaps(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "points": rng.randint(3, 8 + difficulty * 3),
        "first_gap": rng.randint(1, 9 + difficulty),
        "second_gap": rng.randint(1, 9 + difficulty),
    }

@_number_strategy("geometry_g11_liquid_layer")
def _geometry_g11_liquid_layer(difficulty: int, rng: random.Random) -> dict[str, int]:
    length = rng.randint(2, 8 + difficulty)
    width = rng.randint(2, 8 + difficulty)
    layer_mm = rng.randint(1, 8 + difficulty * 2)
    # 1 л = 0,001 м³: V литров на a*b м² дают V/(a*b) мм слоя.
    return {"length": length, "width": width, "volume_litres": length * width * layer_mm}

@_number_strategy("geometry_g12_joined_rectangles")
def _geometry_g12_joined_rectangles(difficulty: int, rng: random.Random) -> dict[str, int]:
    short_side = rng.randint(1, 5 + difficulty)
    long_side = short_side + rng.randint(1, 6 + difficulty)
    return {"long_side": long_side, "short_side": short_side}

@_number_strategy("h04_sequential_cuts")
def _h04_sequential_cuts(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"pieces": rng.randint(3, 8 + difficulty * 8)}

@_number_strategy("h05_cuboid_blocks")
def _h05_cuboid_blocks(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Размеры большого бруса строятся как кратные размерам малого, поэтому
    # разрезание без остатка гарантировано.
    a, b, c = (rng.randint(1, 4 + difficulty // 3) for _ in range(3))
    count_a = rng.randint(2, 3 + difficulty)
    count_b = rng.randint(2, 3 + difficulty)
    count_c = rng.randint(2, 3 + difficulty)
    return {
        "block_a": a,
        "block_b": b,
        "block_c": c,
        "big_a": a * count_a,
        "big_b": b * count_b,
        "big_c": c * count_c,
    }

@_number_strategy("h06_compare_cutting_schemes")
def _h06_compare_cutting_schemes(difficulty: int, rng: random.Random) -> dict[str, int]:
    # Обе схемы используют один и тот же куб: разные числа разбиений по осям
    # дают разные количества брусков и устраняют ответ «поровну».
    side_units = rng.choice([12, 24, 36, 48, 60])
    first_step = rng.choice([1, 2, 3, 4, 6])
    second_step = rng.choice([x for x in [1, 2, 3, 4, 6, 12] if x != first_step and side_units % x == 0])
    return {"side": side_units, "first_step": first_step, "second_step": second_step}

@_number_strategy("h07_painted_cube_odd_faces")
def _h07_painted_cube_odd_faces(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"side": rng.randint(3, 5 + difficulty * 2)}

@_number_strategy("h08_cube_paint_scale")
def _h08_cube_paint_scale(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "base_side": rng.randint(1, 4 + difficulty),
        "base_paint": rng.randint(5, 30 + difficulty * 20),
        "scale": rng.randint(2, min(10, 2 + difficulty)),
    }

@_number_strategy("h03_letter_pi_cells")
def _h03_letter_pi_cells(difficulty: int, rng: random.Random) -> dict[str, int]:
    thickness = rng.randint(1, min(8, 1 + difficulty))
    return {
        "thickness": thickness,
        "width": rng.randint(2 * thickness + 1, 2 * thickness + 10 + difficulty * 4),
        "height": rng.randint(thickness + 1, thickness + 10 + difficulty * 5),
    }

@_number_strategy("h09_cube_face_labels")
def _h09_cube_face_labels(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"side": rng.randint(2, 5 + difficulty * 3)}

@_number_strategy("h01_grid_partitions")
def _h01_grid_partitions(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"rows": rng.randint(2, 20 + difficulty * 40), "cols": rng.randint(2, 20 + difficulty * 40)}

@_number_strategy("h02_grid_partitions_hole")
def _h02_grid_partitions_hole(difficulty: int, rng: random.Random) -> dict[str, int]:
    hole_rows = rng.randint(1, 3 + difficulty * 3)
    hole_cols = rng.randint(1, 3 + difficulty * 3)
    return {
        "hole_rows": hole_rows,
        "hole_cols": hole_cols,
        "rows": hole_rows + rng.randint(2, 10 + difficulty * 12),
        "cols": hole_cols + rng.randint(2, 10 + difficulty * 12),
    }

@_number_strategy("i01_weekday_after_days")
def _i01_weekday_after_days(difficulty: int, rng: random.Random) -> dict[str, Any]:
    return {
        "start_weekday": 0,
        "days": rng.randint(1, 100 + difficulty * 500),
    }

@_number_strategy("i02_weekday_count_month")
def _i02_weekday_count_month(difficulty: int, rng: random.Random) -> dict[str, Any]:
    start_weekday, target_weekday = rng.randrange(7), 0
    return {
        "days": rng.choice([28, 29, 30, 31]),
        "start_weekday": start_weekday,
        "target_weekday": target_weekday,
    }

@_number_strategy("i03_nth_weekday_month")
def _i03_nth_weekday_month(difficulty: int, rng: random.Random) -> dict[str, Any]:
    days, start_weekday, target_weekday = rng.choice([28, 29, 30, 31]), rng.randrange(7), 0
    count = _weekday_count_in_month(days, start_weekday, target_weekday)
    occurrence = rng.randint(1, count)
    return {
        "days": days,
        "start_weekday": start_weekday,
        "target_weekday": target_weekday,
        "occurrence": occurrence,
    }

@_number_strategy("i04_timezone_direct")
def _i04_timezone_direct(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "hour": rng.randrange(24),
        "minute": rng.randrange(60),
        "offset": rng.randint(1, 8),
    }

@_number_strategy("i05_timezone_two_leg")
def _i05_timezone_two_leg(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "hour": rng.randrange(24),
        "minute": rng.randrange(60),
        "offset": rng.randint(2, 8),
        "first_flight": rng.randrange(60, 9 * 60 + 1, 15),
        "wait": rng.randrange(30, 4 * 60 + 1, 15),
        "second_flight": rng.randrange(60, 9 * 60 + 1, 15),
    }

@_number_strategy("i06_turnaround_timezone")
def _i06_turnaround_timezone(difficulty: int, rng: random.Random) -> dict[str, int]:
    ratio = rng.randint(2, 4)
    west_minutes = rng.choice((30, 45, 60, 75, 90))
    # Границы держат время прибытия в том же дне, без неоговорённого перехода даты.
    departure_hour = rng.randint(5, 8)
    departure_minute = rng.choice((0, 15, 30, 45))
    timezone_diff = rng.randint(1, 6)
    arrival_minutes = departure_hour * 60 + departure_minute + west_minutes * (ratio + 1) + timezone_diff * 60
    return {
        "timezone_diff": timezone_diff,
        "departure_hour": departure_hour,
        "departure_minute": departure_minute,
        "arrival_hour": arrival_minutes // 60,
        "arrival_minute": arrival_minutes % 60,
        "east_ratio": ratio,
    }

@_number_strategy("i07_clock_drift")
def _i07_clock_drift(difficulty: int, rng: random.Random) -> dict[str, int]:
    relative_drift = rng.choice((20, 24, 30, 36, 40, 45, 60))
    gain = rng.randint(5, relative_drift - 5)
    loss = relative_drift - gain
    cycle = 720 // math.gcd(720, relative_drift)
    days = rng.randint(1, cycle - 1)
    while math.gcd(days, cycle) != 1:
        days = rng.randint(1, cycle - 1)
    return {"gain_per_day": gain, "loss_per_day": loss, "initial_difference": (-days * relative_drift) % 720}

@_number_strategy("i08_distinct_clock_digits")
def _i08_distinct_clock_digits(difficulty: int, rng: random.Random) -> dict[str, int]:
    start_seconds = rng.randrange(24 * 60 * 60)
    return {
        "start_hour": start_seconds // 3600,
        "start_minute": (start_seconds // 60) % 60,
        "start_second": start_seconds % 60,
        "occurrence": rng.randint(1, min(8, 2 + difficulty)),
    }

@_number_strategy("i01_calendar_date")
def _i01_calendar_date(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Настоящие даты для задач I01 без несуществующих 29 февраля."""
    year = rng.randint(2020, 2040)
    month = rng.randint(1, 12)
    day = rng.randint(1, _days_in_month(year, month))
    return {
        "year": year,
        "month": month,
        "day": day,
        "days": rng.randint(7, 365 + difficulty * 730),
    }

@_number_strategy("i02_calendar_month")
def _i02_calendar_month(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"year": rng.randint(2020, 2040 + difficulty * 6)}

@_number_strategy("i02_may_to_september")
def _i02_may_to_september(difficulty: int, rng: random.Random) -> dict[str, int]:
    # При 31 дне суббот больше пятниц ровно тогда, когда 1 мая — суббота.
    candidates = [
        year for year in range(2020, 2101)
        if _count_weekday_in_month(year, 5, "суббота") > _count_weekday_in_month(year, 5, "пятница")
    ]
    return {"year": rng.choice(candidates)}

@_number_strategy("i03_calendar_year")
def _i03_calendar_year(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"year": rng.randint(2020, 2040 + difficulty * 6)}

@_number_strategy("i03_possible_last_weekday")
def _i03_possible_last_weekday(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {}

@_number_strategy("i04_direct_timezone")
def _i04_direct_timezone(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "timezone_diff": rng.randint(1, 7),
        "departure_hour": rng.randint(0, 23),
        "departure_minute": rng.choice((0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)),
        "duration_minutes": rng.randint(2, 9) * 60 + rng.choice((0, 10, 20, 30, 40, 50)),
    }

@_number_strategy("i05_multi_leg_timezone")
def _i05_multi_leg_timezone(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {
        "ab_diff": rng.randint(0, 4),
        "bc_diff": rng.randint(1, 4),
        "departure_hour": rng.randint(0, 23),
        "departure_minute": rng.choice((0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)),
        "leg_one_minutes": rng.randint(1, 5) * 60 + rng.choice((0, 15, 30, 45)),
        "wait_minutes": rng.choice((30, 45, 60, 75, 90, 120)),
        "leg_two_minutes": rng.randint(1, 5) * 60 + rng.choice((0, 15, 30, 45)),
    }

@_number_strategy("i08_digital_display")
def _i08_digital_display(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"hour": rng.randint(0, 23), "minute": rng.randint(0, 59), "second": rng.randint(0, 59), "occurrence": rng.randint(1, 8)}

@_number_strategy("i08_analog_chimes")
def _i08_analog_chimes(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {"cycles": rng.randint(1, min(3, difficulty // 3 + 1))}

@_number_strategy("j03_catch_up")
def _j03_catch_up(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Строит отрыв как произведение относительной скорости и целого времени."""
    speed_slow = rng.randint(3, min(45, difficulty * 4 + 8))
    speed_fast = speed_slow + rng.randint(1, min(12, 60 - speed_slow))
    catch_time = rng.randint(1, min(12, difficulty + 3))
    return {
        "speed_slow": speed_slow,
        "speed_fast": speed_fast,
        "lead_distance": (speed_fast - speed_slow) * catch_time,
    }

@_number_strategy("j04_three_movers")
def _j04_three_movers(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Подбирает два времени встреч так, чтобы скрытая дистанция восстанавливалась цело."""
    speed_1 = rng.randint(3, min(16, difficulty * 2 + 4))
    speed_2 = rng.randint(2, min(12, difficulty + 4))
    divisors = [value for value in range(1, min(8, speed_1 + speed_2) + 1) if (speed_1 + speed_2) % value == 0]
    speed_3 = speed_2 + rng.choice(divisors)
    time_2 = rng.randint(1, min(5, difficulty // 2 + 2))
    time_3 = time_2 + rng.randint(1, min(6, difficulty // 2 + 2))
    return {
        "speed_1": speed_1,
        "speed_2": speed_2,
        "speed_3": speed_3,
        "time_2": time_2,
        "time_3": time_3,
    }

@_number_strategy("j05_out_and_back")
def _j05_out_and_back(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Подбирает скорости через общий путь, чтобы время возвращения было целым."""
    top_time = min(6, difficulty + 2)
    time_out = rng.randint(1, top_time)
    time_back = rng.randint(1, top_time)
    while time_back == time_out:
        time_back = rng.randint(1, top_time)
    base_speed = rng.randint(3, 10)
    return {
        "speed_out": base_speed * time_back,
        "speed_back": base_speed * time_out,
        "time_out": time_out,
    }

@_number_strategy("j06_average_speed")
def _j06_average_speed(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Строит разные скорости вокруг средней, сохраняя точное d_общ / t_общ."""
    top_time = min(6, difficulty + 2)
    time_1 = rng.randint(1, top_time)
    time_2 = rng.randint(1, top_time)
    step = rng.randint(1, 3)
    average_speed = rng.randint(time_1 * step + 3, 60)
    return {
        "speed_1": average_speed + time_2 * step,
        "time_1": time_1,
        "speed_2": average_speed - time_1 * step,
        "time_2": time_2,
    }

@_number_strategy("j07_circular_meeting")
def _j07_circular_meeting(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Строит длину круга как относительную скорость, умноженную на целое время."""
    speed_slow = rng.randint(3, min(45, difficulty * 4 + 8))
    speed_fast = speed_slow + rng.randint(1, min(15, 60 - speed_slow))
    meeting_time = rng.randint(1, min(12, difficulty + 3))
    return {
        "track_length": (speed_fast - speed_slow) * meeting_time,
        "speed_slow": speed_slow,
        "speed_fast": speed_fast,
    }

@_number_strategy("k02_one_wrong_equation")
def _k02_one_wrong_equation(difficulty: int, rng: random.Random) -> dict[str, int]:
    """Строит три линейных равенства из целого ответа; ошибочна ровно одна строка."""
    x = rng.randint(6, 25 + difficulty * 12)
    multipliers = rng.sample(range(3, 10 + difficulty), 3)
    multiplier_1, multiplier_2, multiplier_3 = multipliers
    wrong_offset = rng.randint(1, 3 + difficulty)
    return {
        "x": x,
        "multiplier_1": multiplier_1,
        "multiplier_2": multiplier_2,
        "multiplier_3": multiplier_3,
        "result_1": x * multiplier_1,
        "result_2": x * multiplier_2,
        "result_3": x * multiplier_3 + wrong_offset,
    }

@_number_strategy("k03_elevator_gcd")
def _k03_elevator_gcd(difficulty: int, rng: random.Random) -> dict[str, int]:
    return _k_gcd_reachability_numbers(difficulty, rng)

@_number_strategy("k08_transform_gcd")
def _k08_transform_gcd(difficulty: int, rng: random.Random) -> dict[str, int]:
    return _k_gcd_reachability_numbers(difficulty, rng)

@_number_strategy("k04_domino_parity")
def _k04_domino_parity(difficulty: int, rng: random.Random) -> dict[str, int]:
    rows = rng.randint(3, 4 + difficulty)
    columns = rng.randint(3, 4 + difficulty)
    return {"rows": rows, "columns": columns}

@_number_strategy("k05_progression_invariant")
def _k05_progression_invariant(difficulty: int, rng: random.Random) -> dict[str, int]:
    count = rng.randint(4, 7 + difficulty)
    step = rng.randint(1, 2 + difficulty)
    possible = rng.choice((False, True))
    first = rng.randint(1, 8 + difficulty * 3)
    total = count * (2 * first + (count - 1) * step) // 2
    if not possible:
        total += rng.choice((1, 2, 3, 5))
        while _k_progression_sum_possible(count, step, total) == "можно":
            total += 1
    return {"count": count, "step": step, "total": total}

@_number_strategy("k06_guaranteed_draws")
def _k06_guaranteed_draws(difficulty: int, rng: random.Random) -> dict[str, int]:
    red = rng.randint(2, 5 + difficulty)
    blue = rng.randint(2, 5 + difficulty)
    green = rng.randint(2, 5 + difficulty)
    total = red + blue + green
    return {
        "total": total,
        "red_draw": total - red + 1,
        "blue_draw": total - blue + 1,
        "red": red,
        "blue": blue,
        "green": green,
    }

@_number_strategy("k01_fixed_truth_liars")
def _k01_fixed_truth_liars(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {}

@_number_strategy("k07_fixed_order_clues")
def _k07_fixed_order_clues(difficulty: int, rng: random.Random) -> dict[str, int]:
    return {}

def _numbers(strategy: str, difficulty: int, rng: random.Random) -> dict[str, int]:
    try:
        builder = _NUMBER_STRATEGIES[strategy]
    except KeyError:
        raise ValueError(f"Неизвестная стратегия чисел: {strategy}.") from None
    return builder(difficulty, rng)


def registered_strategies() -> frozenset[str]:
    """Имена всех зарегистрированных стратегий подбора чисел."""
    return frozenset(_NUMBER_STRATEGIES)


def _normalize_answer(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [_normalize_answer(item) for item in value]
    return value


def evaluate_formula(formula: str, variables: dict[str, Any]) -> Any:
    """Безопасно вычисляет ответ шаблона.

    Поддерживает арифметику (`+ - * / // % **`, унарный `-`), строки, разрешённые
    функции из `_FUNCTIONS` и списки/кортежи для ответов из нескольких частей
    (`answer_type = "multi"`). Возвращает int/float, str или list.
    """
    def visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
            return node.value
        if isinstance(node, ast.Name) and node.id in variables:
            return variables[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (not isinstance(right, int) or not 0 <= right <= 64):
                raise ValueError("Степень в answer_formula допускает только целый показатель 0..64.")
            return _OPERATORS[type(node.op)](left, right)
        if isinstance(node, (ast.Tuple, ast.List)):
            return [visit(element) for element in node.elts]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            function = _FUNCTIONS.get(node.func.id)
            if function is None:
                raise ValueError(f"Функция {node.func.id} не разрешена в answer_formula.")
            return function(*[visit(argument) for argument in node.args])
        raise ValueError("В answer_formula допустимы только числа, строки, переменные, арифметика и разрешённые функции.")
    return _normalize_answer(visit(ast.parse(formula, mode="eval")))


def _render(template: dict[str, Any], variables: dict[str, Any]) -> str:
    rendered = dict(variables)
    for name, rule in template.get("derived_words", {}).items():
        rendered[name] = pluralize_ru(int(variables[rule["number"]]), tuple(rule["forms"]))
    try:
        return template["template_text"].format(**rendered)
    except KeyError as error:
        raise ValueError(f"Для шаблона {template['template_id']} не найдена переменная {error.args[0]}.") from error


def _validate_number_constraints(template: dict[str, Any], variables: dict[str, Any]) -> None:
    for name, rule in template.get("constraints", {}).items():
        value = variables.get(name)
        if rule.get("type") == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"Шаблон {template['template_id']} создал нецелое значение {name}.")
        if (("min" in rule and value < rule["min"])
                or ("max" in rule and value > rule["max"])):
            raise ValueError(f"Шаблон {template['template_id']} создал {name} вне constraints.")


def generate_problem_from_template(module: str, difficulty: int, *, rng: random.Random | None = None, index: int = 1) -> GeneratedTemplateProblem:
    chooser = rng or random.Random()
    candidates = find_templates(module, difficulty)
    if not candidates:
        raise ValueError(f"Для темы '{module}' и сложности {difficulty} нет шаблонов.")
    template = chooser.choice(candidates)
    variables = _numbers(template["number_strategy"], difficulty, chooser)
    _validate_number_constraints(template, variables)
    character_slots = template.get("placeholders", {}).get("characters", [])
    if character_slots:
        context = sample_story_context(chooser, min_characters=len(character_slots), max_characters=len(character_slots))
        variables.update(dict(zip(character_slots, context.characters, strict=True)))
        variables["story_world"] = context.world_title
        variables["location"] = context.location
    answer = evaluate_formula(template["answer_formula"], variables)
    answer_type = template.get("answer_type", "number")
    if answer_type == "number" and template.get("integer_answer_required") and not isinstance(answer, int):
        raise ValueError(f"Шаблон {template['template_id']} дал нецелый ответ.")
    if answer_type == "multi" and not isinstance(answer, list):
        raise ValueError(f"Шаблон {template['template_id']} с answer_type=multi должен вернуть список.")
    return GeneratedTemplateProblem(
        id=f"generated_{module}_{index:05d}", template_id=template["template_id"], domain=template["domain"],
        module=template["module"], topic=template["topic"], difficulty=difficulty,
        problem_text=_render(template, variables), answer=answer, variables=variables,
    )
