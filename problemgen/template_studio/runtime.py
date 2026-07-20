"""Детерминированная генерация экземпляра активного Studio-шаблона."""

from __future__ import annotations

import random
import re
from fractions import Fraction
from typing import Any

from .safe_expressions import SafeExpressionError, evaluate_expression


PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
SUPPORTED_PARAMETER_TYPES = frozenset({
    "integer", "positive_integer", "nonnegative_integer", "decimal", "fraction",
    "boolean", "string", "word", "letter", "name", "choice", "integer_list", "word_list",
})
SUPPORTED_ANSWER_TYPES = frozenset({"integer", "number", "decimal", "fraction", "boolean", "text", "list"})
MAX_RANGE = 100_000


class TemplateRuntimeError(ValueError):
    """Данные шаблона нельзя безопасно сгенерировать или отрендерить."""


def generate_active_template(template: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    values = sample_parameters(template.get("parameter_schema", {}), rng)
    values.update(derive_values(template.get("derived_values", {}), values))
    answer = evaluate_expression(template.get("answer_expression", ""), values)
    rendered = render_template(str(template.get("candidate_template_text", "")), values)
    return {"rendered_problem": rendered, "parameters": values, "answer": normalize_value(answer)}


def sample_parameters(schema: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    if not isinstance(schema, dict):
        raise TemplateRuntimeError("Схема параметров должна быть JSON-объектом.")
    values: dict[str, Any] = {}
    for name, rule in schema.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise TemplateRuntimeError("Имена параметров должны быть ASCII-идентификаторами.")
        if not isinstance(rule, dict):
            raise TemplateRuntimeError(f"Описание параметра {name} должно быть объектом.")
        kind = rule.get("type")
        if kind not in SUPPORTED_PARAMETER_TYPES:
            raise TemplateRuntimeError(f"Неподдерживаемый тип параметра {kind!r}.")
        values[name] = _sample_value(name, rule, rng)
    return values


def derive_values(expressions: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(expressions, dict):
        raise TemplateRuntimeError("Derived values должны быть объектом с выражениями.")
    remaining = {name: expression for name, expression in expressions.items()}
    derived: dict[str, Any] = {}
    while remaining:
        progress = False
        for name, expression in list(remaining.items()):
            try:
                derived[name] = evaluate_expression(str(expression), {**values, **derived})
            except SafeExpressionError as error:
                if "Неизвестная переменная" in str(error):
                    continue
                raise TemplateRuntimeError(f"Derived-параметр {name}: {error}") from error
            del remaining[name]
            progress = True
        if not progress:
            names = ", ".join(sorted(remaining))
            raise TemplateRuntimeError(f"Неразрешённая или циклическая зависимость derived-параметров: {names}.")
    # Внутри генерации сохраняем точные Fraction: следующий derived-параметр
    # может зависеть от этого значения. В JSON они преобразуются только на
    # границе preview/site API через normalize_value().
    return derived


def render_template(template_text: str, values: dict[str, Any]) -> str:
    if not isinstance(template_text, str) or not template_text.strip() or len(template_text) > 20_000:
        raise TemplateRuntimeError("Текст шаблона должен быть непустой строкой не длиннее 20000 символов.")
    missing = sorted(set(PLACEHOLDER_RE.findall(template_text)) - set(values))
    if missing:
        raise TemplateRuntimeError(f"Не определены плейсхолдеры: {', '.join(missing)}.")
    if re.search(r"\{[^{}]+\}", template_text) and not PLACEHOLDER_RE.search(template_text):
        raise TemplateRuntimeError("В тексте есть плейсхолдер недопустимого формата.")
    rendered = template_text.format(**{name: display_value(value) for name, value in values.items()})
    if "{" in rendered or "}" in rendered:
        raise TemplateRuntimeError("После рендеринга остались неразрешённые плейсхолдеры.")
    return rendered


def answer_type_matches(answer: Any, answer_type: str) -> bool:
    if answer_type == "integer":
        return isinstance(answer, int) and not isinstance(answer, bool)
    if answer_type in {"number", "decimal"}:
        return isinstance(answer, (int, float, Fraction)) and not isinstance(answer, bool)
    if answer_type == "fraction":
        return isinstance(answer, (int, float, Fraction, str)) and not isinstance(answer, bool)
    if answer_type == "boolean":
        return isinstance(answer, bool)
    if answer_type == "text":
        return isinstance(answer, str)
    if answer_type == "list":
        return isinstance(answer, (list, tuple))
    return False


def display_value(value: Any) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, list):
        return ", ".join(display_value(item) for item in value)
    return str(value)


def normalize_value(value: Any) -> Any:
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, tuple):
        return [normalize_value(item) for item in value]
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    return value


def _sample_value(name: str, rule: dict[str, Any], rng: random.Random) -> Any:
    kind = rule["type"]
    allowed = rule.get("allowed_values", rule.get("values"))
    if kind in {"choice", "string", "word", "letter", "name", "integer_list", "word_list"}:
        if not isinstance(allowed, list) or not allowed:
            raise TemplateRuntimeError(f"Параметр {name} типа {kind} требует непустой allowed_values.")
        picked = rng.choice(allowed)
        if kind == "letter" and (not isinstance(picked, str) or len(picked) != 1):
            raise TemplateRuntimeError(f"Параметр {name} типа letter принимает только отдельные буквы.")
        if kind == "integer_list" and (not isinstance(picked, list) or any(not isinstance(item, int) for item in picked)):
            raise TemplateRuntimeError(f"Параметр {name} типа integer_list требует списки целых чисел.")
        if kind == "word_list" and (not isinstance(picked, list) or any(not isinstance(item, str) for item in picked)):
            raise TemplateRuntimeError(f"Параметр {name} типа word_list требует списки слов.")
        return picked
    if kind == "boolean":
        return bool(rng.randrange(2))
    minimum, maximum = _numeric_bounds(name, rule, kind)
    if kind == "decimal":
        return rng.randint(int(minimum * 10), int(maximum * 10)) / 10
    if kind == "fraction":
        denominator = rng.randint(2, 12)
        numerator = rng.randint(int(minimum * denominator), int(maximum * denominator))
        return Fraction(numerator, denominator)
    return rng.randint(int(minimum), int(maximum))


def _numeric_bounds(name: str, rule: dict[str, Any], kind: str) -> tuple[float, float]:
    default_minimum = 1 if kind == "positive_integer" else 0 if kind == "nonnegative_integer" else -100
    minimum = rule.get("minimum", rule.get("min", default_minimum))
    maximum = rule.get("maximum", rule.get("max", 100))
    if isinstance(minimum, bool) or isinstance(maximum, bool) or not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        raise TemplateRuntimeError(f"Параметр {name} требует числовые minimum и maximum.")
    if minimum > maximum or maximum - minimum > MAX_RANGE:
        raise TemplateRuntimeError(f"Диапазон параметра {name} некорректен или слишком велик.")
    return float(minimum), float(maximum)
