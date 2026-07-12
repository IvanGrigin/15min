from __future__ import annotations

import ast
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
    answer: int | float
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
    rabbits = rng.randint(1, max(2, difficulty + 1))
    ducks = rng.randint(1, max(2, difficulty + 2))
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
    total = rng.randint(5, difficulty * 25 + 25) * 200
    loan = rng.randint(5, difficulty * 30 + 30) * 100
    paid_2 = rng.randint(100, total // 2 + loan // 2 - 1)
    return {"total": total, "loan": loan, "paid_2": paid_2}


@_number_strategy("movement_together")
def _movement_together(difficulty: int, rng: random.Random) -> dict[str, int]:
    top = min(30, difficulty * 3 + 3)
    return {"speed_1": rng.randint(1, top), "speed_2": rng.randint(1, top), "duration": rng.randint(1, min(8, difficulty + 1))}


def _numbers(strategy: str, difficulty: int, rng: random.Random) -> dict[str, int]:
    try:
        builder = _NUMBER_STRATEGIES[strategy]
    except KeyError:
        raise ValueError(f"Неизвестная стратегия чисел: {strategy}.") from None
    return builder(difficulty, rng)


def registered_strategies() -> frozenset[str]:
    """Имена всех зарегистрированных стратегий подбора чисел."""
    return frozenset(_NUMBER_STRATEGIES)


def evaluate_formula(formula: str, variables: dict[str, Any]) -> int | float:
    def visit(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id in variables:
            return variables[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError("В answer_formula допустимы только числа, переменные и арифметические операции.")
    answer = visit(ast.parse(formula, mode="eval"))
    return int(answer) if isinstance(answer, float) and answer.is_integer() else answer


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
    if template.get("integer_answer_required") and not isinstance(answer, int):
        raise ValueError(f"Шаблон {template['template_id']} дал нецелый ответ.")
    return GeneratedTemplateProblem(
        id=f"generated_{module}_{index:05d}", template_id=template["template_id"], domain=template["domain"],
        module=template["module"], topic=template["topic"], difficulty=difficulty,
        problem_text=_render(template, variables), answer=answer, variables=variables,
    )
