from __future__ import annotations

import ast
import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "docs" / "02_uravneniya_i_neravenstva_without_1502.md"
DEFAULT_EQUATION_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "equations" / "templates.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
PLACEHOLDER_RE = re.compile(r"{([A-Za-zА-Яа-я_][A-Za-zА-Яа-я0-9_]*)}")
MAX_ATTEMPTS = 3000


class EquationTemplateError(ValueError):
    """Понятная ошибка при загрузке или генерации шаблона уравнений."""


@dataclass(frozen=True)
class GeneratedEquationProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int | dict[str, Any]
    parameters: dict[str, Any]
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "template_id": self.template_id,
            "source_problem_numbers": self.source_problem_numbers,
            "problem_text": self.problem_text,
            "answer": self.answer,
            "parameters": self.parameters,
            "seed": self.seed,
        }


def source_problem_numbers(path: Path = SOURCE_PATH) -> set[int]:
    numbers: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = NUMBERED_LINE_RE.match(line)
        if match:
            numbers.add(int(match.group(1)))
    return numbers


def _format_int(value: int | Fraction) -> str:
    if isinstance(value, Fraction):
        if value.denominator != 1:
            raise EquationTemplateError(f"Ожидалось целое число, получено {value}.")
        value = value.numerator
    return str(int(value))


def _render(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise EquationTemplateError(f"Нет значения для {key}.")
        return str(values[key])

    rendered = PLACEHOLDER_RE.sub(replace, template)
    if "{" in rendered or "}" in rendered:
        raise EquationTemplateError("В условии остались незаполненные плейсхолдеры.")
    if "+ -" in rendered or "- -" in rendered:
        raise EquationTemplateError(f"Плохая комбинация знаков в условии: {rendered}")
    return rendered


def _to_python_expression(expr: str) -> str:
    return (
        expr.replace("−", "-")
        .replace("×", "*")
        .replace("·", "*")
        .replace(":", "/")
        .replace(" ", "")
    )


def _eval_ast(node: ast.AST, variables: dict[str, Fraction]) -> Fraction:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, variables)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return Fraction(node.value, 1)
    if isinstance(node, ast.Name) and node.id in variables:
        return variables[node.id]
    if isinstance(node, ast.UnaryOp):
        value = _eval_ast(node.operand, variables)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return value
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left, variables)
        right = _eval_ast(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise EquationTemplateError("Деление на ноль.")
            return left / right
    raise EquationTemplateError(f"Недопустимое выражение: {ast.dump(node)}")


def evaluate_expression(expr: str, **variables: int) -> Fraction:
    tree = ast.parse(_to_python_expression(expr), mode="eval")
    return _eval_ast(tree, {key: Fraction(value, 1) for key, value in variables.items()})


def _candidate_solutions(expr: str, rng: random.Random) -> list[int]:
    normalized = _to_python_expression(expr)
    structured_values = list(_structured_candidate_pool(normalized))
    if structured_values:
        rng.shuffle(structured_values)
        random_values: list[int] = []
        seen = set(structured_values)
        while len(random_values) < 200:
            value = rng.randint(-10000, 10000)
            if value and value not in seen:
                random_values.append(value)
                seen.add(value)
        return structured_values + random_values
    random_values = []
    seen: set[int] = set()
    while len(random_values) < 1000:
        value = rng.randint(-10000, 10000)
        if value and value not in seen:
            random_values.append(value)
            seen.add(value)
    return random_values


@lru_cache(maxsize=1024)
def _structured_candidate_pool(normalized: str) -> tuple[int, ...]:
    numerators = [abs(int(match.group(1))) for match in re.finditer(r"(-?\d+)/x\b", normalized)]
    if numerators:
        divisors = sorted({
            sign * divisor
            for number in numerators
            for divisor in range(1, abs(number) + 1)
            if number % divisor == 0
            for sign in (-1, 1)
        })
        return tuple(value for value in divisors if value != 0)
    denominator_values = [abs(int(match.group(1))) for match in re.finditer(r"/(-?\d+)", normalized)]
    lcm = 1
    for denominator in denominator_values:
        if denominator:
            lcm = math.lcm(lcm, denominator)
    structured_candidates: set[int] = set()
    constants = [int(match.group(0)) for match in re.finditer(r"-?\d+", normalized)]
    if lcm > 1 and lcm <= 10000:
        for base in constants + [0]:
            for step in range(-140, 141):
                candidate = base + step * lcm
                if -10000 <= candidate <= 10000 and candidate != 0:
                    structured_candidates.add(candidate)
    for denominator in denominator_values:
        if 1 < denominator <= 10000:
            for base in constants + [0]:
                for step in range(-140, 141):
                    candidate = base + step * denominator
                    if -10000 <= candidate <= 10000 and candidate != 0:
                        structured_candidates.add(candidate)
    for match in re.finditer(r"\((-?\d+)([+-])(-?\d+)\*x\)/(\d+)", normalized):
        constant = int(match.group(1))
        sign = 1 if match.group(2) == "+" else -1
        coefficient = sign * int(match.group(3))
        denominator = int(match.group(4))
        divisor = math.gcd(abs(coefficient), denominator)
        if (-constant) % divisor != 0:
            continue
        reduced_coefficient = coefficient // divisor
        reduced_denominator = denominator // divisor
        reduced_target = (-constant) // divisor
        residue = (reduced_target * pow(reduced_coefficient % reduced_denominator, -1, reduced_denominator)) % reduced_denominator
        for step in range(-600, 601):
            candidate = residue + step * reduced_denominator
            if -10000 <= candidate <= 10000 and candidate != 0:
                structured_candidates.add(candidate)
    return tuple(sorted(structured_candidates))


def _single_solution_count(expr: str, target: Fraction, expected: int) -> int:
    matches = 0
    for candidate in range(-10000, 10001):
        if candidate == 0 and re.search(r"[/]\s*x\b", _to_python_expression(expr)):
            continue
        try:
            if evaluate_expression(expr, x=candidate) == target:
                matches += 1
                if candidate != expected:
                    return matches + 10
        except EquationTemplateError:
            continue
    return matches


@lru_cache(maxsize=4)
def _load_payload(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_equation_templates(path: str | Path = DEFAULT_EQUATION_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    payload = _load_payload(str(resolved), resolved.stat().st_mtime_ns)
    templates = payload.get("templates")
    if not isinstance(templates, list) or not templates:
        raise EquationTemplateError("В equations problem set нет списка templates.")
    validate_equation_catalog(templates)
    return list(templates)


def validate_equation_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    seen: list[int] = []
    for template in templates:
        for field in ("id", "problem_type", "source_problem_numbers", "render_template", "generation_strategy"):
            if field not in template:
                raise EquationTemplateError(f"У шаблона нет поля {field}: {template!r}")
        template_id = str(template["id"])
        if template_id in ids:
            raise EquationTemplateError(f"Повторяющийся id шаблона: {template_id}")
        ids.add(template_id)
        seen.extend(int(number) for number in template["source_problem_numbers"])
    source = source_problem_numbers()
    if 1502 in seen:
        raise EquationTemplateError("Проблема 1502 не должна входить в equation templates.")
    if set(seen) != source:
        missing = sorted(source - set(seen))
        extra = sorted(set(seen) - source)
        raise EquationTemplateError(f"Проблема покрытия источника. missing={missing}, extra={extra}")
    duplicates = sorted(number for number, count in Counter(seen).items() if count > 1)
    if duplicates:
        raise EquationTemplateError(f"Номера источника встречаются дважды: {duplicates}")


def equation_template_metadata() -> dict[str, Any]:
    templates = load_equation_templates()
    return {
        "modules": [{
            "module_id": "equations",
            "title": "Equations",
            "display_name": "Equations",
            "template_count": len(templates),
            "covered_source_problem_numbers": len(source_problem_numbers()),
        }],
        "templates": [
            {
                "template_id": template["id"],
                "title": template.get("title", template["id"]),
                "display_name": template.get("title", template["id"]),
                "module_name": "Equations",
                "source_problem_numbers": template["source_problem_numbers"],
                "problem_type": template["problem_type"],
            }
            for template in templates
        ],
        "stats": {
            "total_modules": 1,
            "total_templates": len(templates),
            "covered_source_problem_numbers": len(source_problem_numbers()),
            "source_file": "docs/02_uravneniya_i_neravenstva_without_1502.md",
        },
    }


def get_equation_template(template_id: str) -> dict[str, Any]:
    for template in load_equation_templates():
        if template["id"] == template_id:
            return template
    raise EquationTemplateError(f"Неизвестный шаблон уравнений: {template_id}.")


def _generate_single_equation(template: dict[str, Any], rng: random.Random) -> GeneratedEquationProblem:
    expr = str(template["x_expression"])
    result_side = str(template["result_side"])
    last_error: Exception | None = None
    parsed_expr = ast.parse(_to_python_expression(expr), mode="eval")
    for x_solution in _candidate_solutions(expr, rng)[:MAX_ATTEMPTS]:
        try:
            target = _eval_ast(parsed_expr, {"x": Fraction(x_solution, 1)})
            if target.denominator != 1:
                continue
            result_text = _format_int(target)
            rendered = _render(str(template["render_template"]), {"result": result_text})
            return GeneratedEquationProblem(
                module="equations",
                template_id=str(template["id"]),
                source_problem_numbers=list(template["source_problem_numbers"]),
                problem_text=rendered,
                answer=int(x_solution),
                parameters={"x_solution": x_solution, "derived_result": int(target), "result_side": result_side},
            )
        except Exception as error:  # noqa: BLE001
            last_error = error
    raise EquationTemplateError(f"Не удалось построить уравнение {template['id']}: {last_error}")


def _generate_inequality(template: dict[str, Any], rng: random.Random) -> GeneratedEquationProblem:
    answer = rng.randint(4, 80)
    variant = str(template.get("inequality_variant", "difference_product"))
    if variant == "difference_product":
        divisor = rng.choice([6, 8, 10, 12])
        quotient = rng.randint(2, 9)
        extra = rng.randint(20, 90)
        while True:
            denom_left = rng.randint(100, 600)
            denom = denom_left + quotient
            delta = rng.randint(3, 12)
            if (answer * denom) % delta == 0:
                multiplier = answer * denom // delta
                break
        while multiplier <= 0:
            delta = rng.randint(3, 12)
            multiplier = answer * denom // delta
        values = {
            "a": extra + delta,
            "b": extra,
            "c": multiplier,
            "d": denom_left,
            "e": quotient * divisor,
            "f": divisor,
        }
    else:
        divisor = rng.choice([3, 4, 6, 9])
        quotient = rng.randint(5, 15)
        denom_left = rng.randint(200, 800)
        denom = denom_left - quotient
        first = rng.randint(2, 20)
        second = rng.randint(first + 20, first + 200)
        while True:
            delta = rng.randint(5, 18)
            if (answer * denom) % delta == 0:
                third = second - first + delta
                multiplier = answer * denom // delta
                break
        values = {
            "a": first,
            "b": second,
            "c": third,
            "d": multiplier,
            "e": denom_left,
            "f": quotient * divisor,
            "g": divisor,
        }
    text = _render(str(template["render_template"]), values)
    return GeneratedEquationProblem(
        module="equations",
        template_id=str(template["id"]),
        source_problem_numbers=list(template["source_problem_numbers"]),
        problem_text=text,
        answer=answer,
        parameters={**values, "greatest_natural_solution": answer},
    )


def _system_rhs(a: int, b: int, x: int, y: int) -> int:
    return a * x + b * y


def _generate_systems(template: dict[str, Any], rng: random.Random) -> GeneratedEquationProblem:
    values: dict[str, Any] = {}
    answers: dict[str, dict[str, int]] = {}
    system_count = int(template.get("system_count", 2))
    for index, label in enumerate(("a", "b")[:system_count], start=1):
        x_value = rng.randint(-12, 12) or 5
        y_value = rng.randint(-12, 12) or -4
        a1, b1, a2, b2 = rng.randint(1, 7), rng.randint(1, 7), rng.randint(1, 7), rng.randint(1, 7)
        while a1 * b2 - a2 * b1 == 0:
            a2, b2 = rng.randint(1, 7), rng.randint(1, 7)
        values.update({
            f"a{index}1": a1, f"b{index}1": b1, f"c{index}1": _system_rhs(a1, b1, x_value, y_value),
            f"a{index}2": a2, f"b{index}2": b2, f"c{index}2": _system_rhs(a2, b2, x_value, y_value),
        })
        answers["а" if label == "a" else "б"] = {"x": x_value, "y": y_value}
    text = _render(str(template["render_template"]), values)
    return GeneratedEquationProblem(
        module="equations",
        template_id=str(template["id"]),
        source_problem_numbers=list(template["source_problem_numbers"]),
        problem_text=text,
        answer=answers,
        parameters=values,
    )


def _generate_multipart(template: dict[str, Any], rng: random.Random) -> GeneratedEquationProblem:
    values: dict[str, Any] = {}
    answers: dict[str, int] = {}
    for part in template["parts"]:
        label = part["label"]
        generated = _generate_single_equation(
            {
                **template,
                "id": f"{template['id']}_{label}",
                "x_expression": part["x_expression"],
                "result_side": part["result_side"],
                "render_template": part["render_template"],
            },
            rng,
        )
        key = f"part_{label}"
        values[key] = generated.problem_text
        answers[label] = int(generated.answer)
    text = _render(str(template["render_template"]), values)
    return GeneratedEquationProblem(
        module="equations",
        template_id=str(template["id"]),
        source_problem_numbers=list(template["source_problem_numbers"]),
        problem_text=text,
        answer=answers,
        parameters=values,
    )


def generate_equation_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedEquationProblem:
    template = get_equation_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    strategy = template["generation_strategy"]
    if strategy == "single_equation_from_integer_solution":
        return _generate_single_equation(template, local_rng)
    if strategy == "inequality_greatest_natural":
        return _generate_inequality(template, local_rng)
    if strategy == "two_linear_systems":
        return _generate_systems(template, local_rng)
    if strategy == "multipart_equations":
        return _generate_multipart(template, local_rng)
    raise EquationTemplateError(f"Неизвестная стратегия уравнений: {strategy}")


def generate_equation_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedEquationProblem:
    if module_id != "equations":
        raise EquationTemplateError(f"Неизвестный модуль уравнений: {module_id}")
    template = rng.choice(load_equation_templates())
    return generate_equation_problem(str(template["id"]), rng=rng)
