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


_OPERATORS: dict[type[ast.AST], Any] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}

_WEEKDAYS_RU = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")


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
    "weekday_of_date": _weekday_of_date,
    "days_in_month": _days_in_month,
    "count_weekday_in_month": _count_weekday_in_month,
    "weekday_after_date": _weekday_after_date,
    "nth_weekday_of_month": _nth_weekday_of_month,
    "possible_last_weekday_ordinals": _possible_last_weekday_ordinals,
    "format_clock_time": _format_clock_time,
    "bigger_label": lambda x, y: "первое" if x > y else ("второе" if y > x else "поровну"),
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
