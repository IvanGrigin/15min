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


def years_to_same_weekday(year: int, month: int, day: int) -> int:
    """Через сколько лет эта же дата снова придётся на тот же день недели.

    Обычный год сдвигает день недели на единицу, високосный — на две, поэтому
    ответ зависит от того, сколько високосных лет попадёт в промежуток:
    выходит 5, 6 или 11 лет. Спрашивать «наименьшую возможную разницу»
    без указания года бессмысленно — она всегда равна пяти, и задача
    решалась бы угадыванием.
    """
    weekday = date(year, month, day).weekday()
    for ahead in range(1, 30):
        if date(year + ahead, month, day).weekday() == weekday:
            return ahead
    raise CalendarPuzzleError(f"От {year} года повтор дня недели не найден.")
