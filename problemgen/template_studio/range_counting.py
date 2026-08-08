"""Подсчёт чисел на промежутке с условием на цифры.

В корпусе это целое семейство: «Сколько нечётных чисел в промежутке от 215
до 983, содержащих цифру 7?», «Сколько в промежутке от 459 до 931 чисел,
не содержащих цифру 3?», «Сколько чётных чисел от 222 до 888 содержат хотя бы
одну цифру 7?».

В библиотеке уже были подсчёты по разрядности — «сколько трёхзначных чисел
не содержат цифру 5». Приём там другой: границы совпадают с границами разряда,
и всё считается умножением по позициям. Как только промежуток произвольный,
позиционная формула перестаёт работать: у 215 и 983 разное число «свободных»
разрядов, и края приходится разбирать отдельно.

Поэтому здесь честный перебор. Промежутки в задачах корпуса не выходят за
несколько тысяч, перебор мгновенный, а формула, которую пришлось бы выводить,
заняла бы страницу и не проверялась бы ничем.

Правила подобраны так, чтобы ответ никогда не был ни нулём, ни всем
промежутком целиком: и то и другое означает, что условие ничего не отбирает.
"""
from __future__ import annotations

# Промежутки корпуса не длиннее нескольких тысяч; предел стоит затем, чтобы
# случайный жребий не превратил генерацию задачи в долгий счёт.
MAX_SPAN = 20_000

# Отбор по самому числу: чётность или последняя цифра. Название поля
# осталось «parity» ради шаблонов, написанных раньше, но отборов больше:
# в корпусе спрашивают и про числа, оканчивающиеся на пять или на ноль.
PARITIES = {
    "any": lambda value: True,
    "even": lambda value: value % 2 == 0,
    "odd": lambda value: value % 2 == 1,
    "ends_0": lambda value: value % 10 == 0,
    "ends_5": lambda value: value % 10 == 5,
}
DIGIT_RULES = {
    "any": lambda text, digit: True,
    "contains": lambda text, digit: digit in text,
    "without": lambda text, digit: digit not in text,
}


class RangeCountError(ValueError):
    """Описание подсчёта на промежутке нельзя разыграть или проверить."""


def check_rule(parity: object, digit_rule: object) -> tuple[str, str]:
    """Проверить, что шаблон просит известные правила отбора."""
    if not isinstance(parity, str) or parity not in PARITIES:
        raise RangeCountError(
            f"Неизвестная чётность {parity!r}. Доступны: {', '.join(sorted(PARITIES))}.")
    if not isinstance(digit_rule, str) or digit_rule not in DIGIT_RULES:
        raise RangeCountError(
            f"Неизвестное правило по цифре {digit_rule!r}. "
            f"Доступны: {', '.join(sorted(DIGIT_RULES))}.")
    return parity, digit_rule


def count_in_range(
    low: int, high: int, *, parity: str, digit_rule: str, digit: int,
    multiple_of: int = 1,
) -> int:
    """Сколько чисел промежутка удовлетворяют всем условиям сразу.

    Промежуток берётся замкнутым: «от 215 до 983» в задачах корпуса включает
    оба конца. Где источник говорит «больше 215, но меньше 983», шаблон
    передаёт уже сдвинутые границы — это его дело, а не решателя.
    """
    check_rule(parity, digit_rule)
    if not isinstance(low, int) or not isinstance(high, int) or low > high:
        raise RangeCountError(f"Промежуток задан неверно: от {low!r} до {high!r}.")
    if high - low > MAX_SPAN:
        raise RangeCountError(f"Промежуток длиннее {MAX_SPAN} — перебор слишком долгий.")
    if not isinstance(digit, int) or not 0 <= digit <= 9:
        raise RangeCountError(f"Цифра должна быть от 0 до 9, получено {digit!r}.")
    if not isinstance(multiple_of, int) or multiple_of < 1:
        raise RangeCountError(f"Делитель должен быть натуральным, получено {multiple_of!r}.")

    keep_parity = PARITIES[parity]
    keep_digit = DIGIT_RULES[digit_rule]
    mark = str(digit)
    return sum(
        1 for value in range(low, high + 1)
        if keep_parity(value) and value % multiple_of == 0 and keep_digit(str(value), mark)
    )


def span_size(low: int, high: int, *, parity: str, multiple_of: int = 1) -> int:
    """Сколько чисел промежутка проходят отбор до условия на цифру.

    Нужно шаблону, чтобы отбраковать вырожденные случаи: если условие на цифру
    оставляет всё или не оставляет ничего, задача не про цифры.
    """
    keep_parity = PARITIES[parity]
    return sum(
        1 for value in range(low, high + 1)
        if keep_parity(value) and value % multiple_of == 0
    )


def max_digit_sum_in_range(low: int, high: int) -> tuple[int, int, int]:
    """Наибольшая сумма цифр на отрезке: сама сумма, число и сколько их таких.

    Перебирать миллионы чисел незачем. Больше всего девяток даёт число,
    у которого верхний кусок совпадает с границей, одна цифра на единицу
    меньше, а хвост — сплошные девятки; таких кандидатов ровно столько,
    сколько цифр, плюс сама верхняя граница. Лучший из попавших в отрезок
    и даёт ответ.

    Третьим числом возвращается, сколько всего чисел отрезка набирают эту
    сумму: при двух и более вопрос «у какого числа» теряет единственный
    ответ, и жеребьёвку надо отбросить.
    """
    if low > high:
        raise ValueError(f"Пустой промежуток: от {low} до {high}.")

    def digit_sum(value: int) -> int:
        return sum(int(digit) for digit in str(value))

    digits = str(high)
    candidates = [high]
    for position, digit in enumerate(digits):
        if digit == "0":
            continue
        head = digits[:position] + str(int(digit) - 1)
        candidates.append(int(head + "9" * (len(digits) - position - 1)))
    fitting = [value for value in candidates if low <= value <= high]
    best_sum = max(digit_sum(value) for value in fitting)
    best_value = max(value for value in fitting if digit_sum(value) == best_sum)
    return best_sum, best_value, count_with_digit_sum(low, high, best_sum)


def count_with_digit_sum(low: int, high: int, wanted: int, limit: int = 3) -> int:
    """Сколько чисел отрезка имеют такую сумму цифр; счёт прекращается на limit.

    Считается по разрядам: сколько чисел не больше границы набирают нужную
    сумму. Полный перебор отрезка в миллион чисел был бы слишком медленным
    внутри подбора параметров.
    """
    def upto(bound: int) -> int:
        if bound < 0:
            return 0
        digits = [int(digit) for digit in str(bound)]
        total = 0
        # Свободный хвост: сколько наборов из length цифр дают сумму target.
        cache: dict[tuple[int, int], int] = {}

        def free(length: int, target: int) -> int:
            if target < 0 or target > 9 * length:
                return 0
            if length == 0:
                return 1 if target == 0 else 0
            key = (length, target)
            if key not in cache:
                cache[key] = sum(free(length - 1, target - digit) for digit in range(10))
            return cache[key]

        prefix = 0
        for position, digit in enumerate(digits):
            for smaller in range(digit):
                total += free(len(digits) - position - 1, wanted - prefix - smaller)
            prefix += digit
        return total + (1 if prefix == wanted else 0)

    return min(upto(high) - upto(low - 1), limit)
