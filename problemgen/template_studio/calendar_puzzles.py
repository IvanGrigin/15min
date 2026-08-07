"""Календарные задачи: день недели, номер дня в году, счёт по датам.

Два приёма из корпуса, у которых общая механика — настоящий календарь.

Первый: «В мае было пятниц больше, чем четвергов. Какого числа был первый
понедельник сентября?» Месяц из 31 дня — это ровно четыре недели плюс три
дня, и эти три лишних дня недели встречаются по пять раз, остальные четыре.
Отсюда сравнение числа пятниц и четвергов задаёт день недели первого числа.

Тут есть подвох, из-за которого шаблон нельзя писать наивно: **однозначны
только 14 пар дней недели из 42**. «Понедельников больше, чем четвергов»
выполняется при трёх разных вариантах первого числа, и ответ на дальнейший
вопрос перестаёт быть единственным. Поэтому пара выбирается не свободно,
а из проверенного списка, который считает эта же функция.

Второй: «Сегодня 12 марта 2021 года. Какое число будет через 329 дней?» —
прямой счёт по календарю с високосными годами.

Календарь берётся из стандартной библиотеки: это не текст задачи, а факт
о мире, такой же как разница часовых поясов.
"""
from __future__ import annotations

import calendar
import collections
from datetime import date, timedelta

WEEKDAY_NAMES = (
    "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
)
# Родительный падеж множественного числа — «пятниц больше, чем четвергов».
WEEKDAY_GENITIVE_PLURAL = (
    "понедельников", "вторников", "сред", "четвергов", "пятниц", "суббот", "воскресений",
)
MONTH_PREPOSITIONAL = (
    "", "январе", "феврале", "марте", "апреле", "мае", "июне",
    "июле", "августе", "сентябре", "октябре", "ноябре", "декабре",
)
MONTH_GENITIVE = (
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


# Именительный падеж нужен там, где месяц сам становится ответом:
# «какой месяц мог быть первым» — «январь», а не «января».
MONTH_NOMINATIVE = (
    "", "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
)


class CalendarPuzzleError(ValueError):
    """Календарное условие нельзя разыграть или проверить."""


def weekday_counts(first_weekday: int, days_in_month: int) -> collections.Counter:
    """Сколько раз каждый день недели встречается в месяце."""
    counted: collections.Counter = collections.Counter()
    for offset in range(days_in_month):
        counted[(first_weekday + offset) % 7] += 1
    return counted


def first_weekdays_matching(more: int, less: int, days_in_month: int) -> list[int]:
    """Дни недели первого числа, при которых `more` встречается чаще `less`."""
    return [
        first for first in range(7)
        if weekday_counts(first, days_in_month)[more] > weekday_counts(first, days_in_month)[less]
    ]


def unambiguous_pairs(days_in_month: int) -> list[tuple[int, int]]:
    """Пары дней недели, у которых сравнение задаёт первое число однозначно.

    Для месяца из 31 дня таких пар всего 14 из 42. Остальные оставляют два
    или три варианта, и вопрос «какого числа» перестаёт иметь единственный
    ответ — а ключ печатается один.
    """
    return [
        (more, less)
        for more in range(7) for less in range(7)
        if more != less and len(first_weekdays_matching(more, less, days_in_month)) == 1
    ]


def nth_weekday_of_month(year: int, month: int, weekday: int, occurrence: int) -> int:
    """Число месяца, на которое приходится n-й такой день недели."""
    found = [
        day for day in range(1, calendar.monthrange(year, month)[1] + 1)
        if date(year, month, day).weekday() == weekday
    ]
    if not 1 <= occurrence <= len(found):
        raise CalendarPuzzleError(
            f"В {MONTH_PREPOSITIONAL[month]} нет {occurrence}-го дня недели "
            f"«{WEEKDAY_NAMES[weekday]}».")
    return found[occurrence - 1]


def year_with_first_weekday(month: int, first_weekday: int, since: int = 2024) -> int:
    """Ближайший год, в котором нужный месяц начинается с нужного дня недели.

    Нужен, чтобы задача про «некоторый год» опиралась на настоящий календарь,
    а не на выдуманный: тогда её можно проверить по любому календарю.
    """
    for year in range(since, since + 40):
        if date(year, month, 1).weekday() == first_weekday:
            return year
    raise CalendarPuzzleError(
        f"За 40 лет от {since} не нашлось года, где {MONTH_PREPOSITIONAL[month]} "
        f"начинается с {WEEKDAY_NAMES[first_weekday]}.")


def shift_days(year: int, month: int, day: int, offset: int) -> tuple[int, int, int]:
    """Дата через offset дней — по настоящему календарю, с високосными."""
    try:
        moved = date(year, month, day) + timedelta(days=offset)
    except (ValueError, OverflowError) as error:
        raise CalendarPuzzleError(f"Дата {day}.{month}.{year} + {offset} дней: {error}") from error
    return moved.year, moved.month, moved.day


def day_of_year(year: int, month: int, day: int) -> int:
    """Номер дня в году: 1 февраля — 32-й день."""
    return date(year, month, day).timetuple().tm_yday


def weekday_of(year: int, month: int, day: int) -> int:
    """День недели даты: 0 — понедельник."""
    return date(year, month, day).weekday()

def month_lengths(leap: bool) -> tuple[int, ...]:
    """Длины месяцев обычного и високосного года."""
    return (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def month_run_starts(total_days: int, run_length: int, leap: bool) -> list[int]:
    """С каких месяцев может начинаться цепочка из ``run_length`` месяцев в ``total_days`` дней.

    Цепочка считается по кругу: декабрь-январь-февраль — тоже три месяца
    подряд, и в задачах корпуса такой ответ засчитывается. Возвращаются
    номера месяцев от единицы; ответов бывает несколько, и это часть задачи.
    """
    if not isinstance(run_length, int) or isinstance(run_length, bool) or not 2 <= run_length <= 6:
        raise CalendarPuzzleError(
            f"Цепочка месяцев должна быть длиной от двух до шести, а не {run_length!r}.")
    lengths = month_lengths(leap)
    return [
        start + 1
        for start in range(12)
        if sum(lengths[(start + step) % 12] for step in range(run_length)) == total_days
    ]


def run_total_days(first_month: int, run_length: int, leap: bool) -> int:
    """Сколько дней в цепочке месяцев, начинающейся с данного."""
    lengths = month_lengths(leap)
    return sum(lengths[(first_month - 1 + step) % 12] for step in range(run_length))


def is_palindrome_date(year: int, month: int, day: int) -> bool:
    """Палиндром ли запись даты в формате ддммгггг."""
    written = f"{day:02d}{month:02d}{year:04d}"
    return written == written[::-1]


def palindrome_dates(year_from: int, year_to: int) -> list[tuple[int, int, int]]:
    """Все даты-палиндромы в промежутке лет, включая границы.

    Проверяются только существующие даты: 29.02 берётся лишь в високосный
    год, и это не мелочь — из 29 палиндромов XXI века один приходится
    ровно на 29 февраля 2092 года.
    """
    if year_to < year_from:
        raise CalendarPuzzleError(f"Промежуток лет задан неверно: {year_from} > {year_to}.")
    if year_to - year_from > 400:
        raise CalendarPuzzleError("Промежуток длиннее четырёх веков считать незачем.")
    found = []
    for year in range(year_from, year_to + 1):
        for month in range(1, 13):
            length = month_lengths(year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))[month - 1]
            for day in range(1, length + 1):
                if is_palindrome_date(year, month, day):
                    found.append((year, month, day))
    return found

