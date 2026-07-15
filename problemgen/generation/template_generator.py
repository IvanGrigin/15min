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
    "e_seq_sum": _e_seq_sum,
    "fib_term": _fib_term,
    "weekday_after": lambda start, days: _WEEKDAYS_RU[(int(start) + int(days)) % 7],
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


# --- авторские стратегии группы E: последовательности и закономерности ---

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
