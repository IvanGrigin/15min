from __future__ import annotations

import json
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
SOURCE_PATH = PROJECT_ROOT / "docs" / "03_sistemy_uravneniy_updated.md"
DEFAULT_SYSTEM_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "systems_of_equations" / "templates.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
MAX_ATTEMPTS = 100


class SystemEquationTemplateError(ValueError):
    """Понятная ошибка при загрузке или генерации шаблона систем уравнений."""


@dataclass(frozen=True)
class GeneratedSystemEquationProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: dict[str, int]
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


def source_system_problem_numbers(path: Path = SOURCE_PATH) -> set[int]:
    numbers: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = NUMBERED_LINE_RE.match(line)
        if match:
            numbers.add(int(match.group(1)))
    return numbers


@lru_cache(maxsize=4)
def _load_payload(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_system_equation_templates(path: str | Path = DEFAULT_SYSTEM_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    payload = _load_payload(str(resolved), resolved.stat().st_mtime_ns)
    templates = payload.get("templates")
    if not isinstance(templates, list) or not templates:
        raise SystemEquationTemplateError("В systems_of_equations problem set нет списка templates.")
    validate_system_equation_catalog(templates)
    return list(templates)


def validate_system_equation_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    seen: list[int] = []
    for template in templates:
        for field in ("id", "module_id", "source_problem_numbers", "coefficient_structure", "generation_strategy"):
            if field not in template:
                raise SystemEquationTemplateError(f"У шаблона нет поля {field}: {template!r}")
        template_id = str(template["id"])
        if template_id in ids:
            raise SystemEquationTemplateError(f"Повторяющийся id шаблона: {template_id}")
        ids.add(template_id)
        if template["module_id"] != "systems_of_equations":
            raise SystemEquationTemplateError(f"Неверный module_id у {template_id}: {template['module_id']}")
        seen.extend(int(number) for number in template["source_problem_numbers"])
    source = source_system_problem_numbers()
    if set(seen) != source:
        missing = sorted(source - set(seen))
        extra = sorted(set(seen) - source)
        raise SystemEquationTemplateError(f"Проблема покрытия источника. missing={missing}, extra={extra}")
    duplicates = sorted(number for number, count in Counter(seen).items() if count > 1)
    if duplicates:
        raise SystemEquationTemplateError(f"Номера источника встречаются дважды: {duplicates}")
    duplicate_template = [template for template in templates if set(template["source_problem_numbers"]) == {700, 886}]
    if len(duplicate_template) != 1:
        raise SystemEquationTemplateError("Дубликаты 700 и 886 должны быть в одном шаблоне.")


def system_equation_template_metadata() -> dict[str, Any]:
    templates = load_system_equation_templates()
    return {
        "modules": [{
            "module_id": "systems_of_equations",
            "title": "Systems of Equations",
            "display_name": "Системы уравнений",
            "template_count": len(templates),
            "covered_source_problem_numbers": len(source_system_problem_numbers()),
        }],
        "templates": [
            {
                "template_id": template["id"],
                "title": template.get("title", template["id"]),
                "display_name": template.get("title", template["id"]),
                "module_name": "Системы уравнений",
                "source_problem_numbers": template["source_problem_numbers"],
                "problem_type": template["problem_type"],
            }
            for template in templates
        ],
        "stats": {
            "total_modules": 1,
            "total_templates": len(templates),
            "covered_source_problem_numbers": len(source_system_problem_numbers()),
            "source_file": "docs/03_sistemy_uravneniy_updated.md",
        },
    }


def get_system_equation_template(template_id: str) -> dict[str, Any]:
    for template in load_system_equation_templates():
        if template["id"] == template_id:
            return template
    raise SystemEquationTemplateError(f"Неизвестный шаблон систем уравнений: {template_id}.")


def _signed_nonzero(rng: random.Random, sign: str | None = None) -> int:
    value = rng.randint(2, 9)
    if sign == "positive":
        return value
    if sign == "negative":
        return -value
    return value if rng.choice([True, False]) else -value


def _coefficient(name: str, spec: dict[str, Any], values: dict[str, int], rng: random.Random) -> int:
    mode = spec["mode"]
    if mode == "fixed":
        return int(spec["value"])
    if mode == "random_nonzero":
        return _signed_nonzero(rng, spec.get("sign"))
    if mode == "same_as":
        return values[str(spec["source"])]
    if mode == "opposite_of":
        return -values[str(spec["source"])]
    raise SystemEquationTemplateError(f"Неизвестный режим коэффициента {name}: {mode}")


def _term(coefficient: int, variable: str, *, first: bool) -> str:
    if coefficient == 0:
        raise SystemEquationTemplateError("Нулевые коэффициенты не должны отображаться.")
    abs_value = abs(coefficient)
    body = variable if abs_value == 1 else f"{abs_value}{variable}"
    if first:
        return body if coefficient > 0 else f"-{body}"
    sign = "+" if coefficient > 0 else "-"
    return f"{sign} {body}"


def render_system(a: int, b: int, e: int, c: int, d: int, f: int) -> str:
    first = f"{_term(a, 'X', first=True)} {_term(b, 'Y', first=False)} = {e}"
    second = f"{_term(c, 'X', first=True)} {_term(d, 'Y', first=False)} = {f}"
    rendered = f"Решите систему уравнений: {first}; {second}."
    malformed = ("+ -", "- -", "1X", "-1X", "1Y", "-1Y")
    if any(item in rendered for item in malformed):
        raise SystemEquationTemplateError(f"Некорректное отображение коэффициентов: {rendered}")
    return rendered


def solve_system(a: int, b: int, e: int, c: int, d: int, f: int) -> tuple[Fraction, Fraction, int]:
    determinant = a * d - b * c
    if determinant == 0:
        raise SystemEquationTemplateError("Определитель равен нулю.")
    x_value = Fraction(e * d - b * f, determinant)
    y_value = Fraction(a * f - e * c, determinant)
    return x_value, y_value, determinant


def _coefficients_from_template(template: dict[str, Any], rng: random.Random) -> dict[str, int]:
    structure = template["coefficient_structure"]
    values: dict[str, int] = {}
    for name in ("x1", "y1", "x2", "y2"):
        values[name] = _coefficient(name, structure[name], values, rng)
    return values


def _structure_matches(template: dict[str, Any], values: dict[str, int]) -> bool:
    relationships = template["coefficient_structure"].get("relationships", [])
    for relationship in relationships:
        if relationship == "x2 == x1" and values["x2"] != values["x1"]:
            return False
        if relationship == "y2 == -y1" and values["y2"] != -values["y1"]:
            return False
        if relationship == "y1 != y2" and values["y1"] == values["y2"]:
            return False
    return True


def generate_system_equation_problem(
    template_id: str,
    *,
    seed: int | None = None,
    rng: random.Random | None = None,
) -> GeneratedSystemEquationProblem:
    template = get_system_equation_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    failed_constraints: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        x_solution = local_rng.randint(-20, 20)
        y_solution = local_rng.randint(-20, 20)
        if x_solution == 0 and y_solution == 0:
            failed_constraints.append("оба ответа равны нулю")
            continue
        coefficients = _coefficients_from_template(template, local_rng)
        a, b, c, d = coefficients["x1"], coefficients["y1"], coefficients["x2"], coefficients["y2"]
        determinant = a * d - b * c
        if determinant == 0:
            failed_constraints.append("determinant == 0")
            continue
        if not _structure_matches(template, coefficients):
            failed_constraints.append("coefficient_structure")
            continue
        e = a * x_solution + b * y_solution
        f = c * x_solution + d * y_solution
        if abs(e) > 400 or abs(f) > 400:
            failed_constraints.append("right_side_too_large")
            continue
        solved_x, solved_y, solved_determinant = solve_system(a, b, e, c, d, f)
        if solved_determinant != determinant:
            failed_constraints.append("determinant_mismatch")
            continue
        if solved_x.denominator != 1 or solved_y.denominator != 1:
            failed_constraints.append("fractional_solution")
            continue
        if int(solved_x) != x_solution or int(solved_y) != y_solution:
            failed_constraints.append("solution_mismatch")
            continue
        problem_text = render_system(a, b, e, c, d, f)
        return GeneratedSystemEquationProblem(
            module="systems_of_equations",
            template_id=str(template["id"]),
            source_problem_numbers=list(template["source_problem_numbers"]),
            problem_text=problem_text,
            answer={"x": x_solution, "y": y_solution},
            parameters={
                "x_solution": x_solution,
                "y_solution": y_solution,
                "x_coefficient_1": a,
                "y_coefficient_1": b,
                "x_coefficient_2": c,
                "y_coefficient_2": d,
                "right_side_1": e,
                "right_side_2": f,
                "determinant": determinant,
                "attempt": attempt,
            },
            seed=seed,
        )
    raise SystemEquationTemplateError(
        f"Не удалось построить систему {template_id} за {MAX_ATTEMPTS} попыток. "
        f"seed={seed}, failed_constraints={failed_constraints[-10:]}"
    )


def generate_system_equation_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedSystemEquationProblem:
    if module_id != "systems_of_equations":
        raise SystemEquationTemplateError(f"Неизвестный модуль систем уравнений: {module_id}")
    template = rng.choice(load_system_equation_templates())
    return generate_system_equation_problem(str(template["id"]), rng=rng)
