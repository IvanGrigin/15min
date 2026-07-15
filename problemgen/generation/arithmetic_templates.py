from __future__ import annotations

import json
import math
import random
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARITHMETIC_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "arithmetic" / "templates.json"
LEGACY_ARITHMETIC_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "arithmetic_templates.json"
SOURCE_PROBLEM_NUMBERS = {
    87, 92, 106, 111, 116, 124, 147, 152, 232, 250, 271, 289, 457, 476, 544, 545,
    546, 547, 548, 549, 550, 590, 594, 619, 620, 621, 622, 623, 624, 625, 626,
    627, 628, 709, 825, 826, 827, 859, 897, 902, 907, 917, 947, 952, 1007, 1082,
    1101, 1108, 1118, 1123, 1124, 1125, 1133, 1174, 1196, 1214, 1226, 1231,
    1233, 1245, 1261, 1323, 1324, 1325, 1333, 1374, 1414, 1426, 1431, 1433,
    1445, 1461, 1522, 1523, 1524,
}
PLACEHOLDER_RE = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")
MAX_ATTEMPTS = 200


class ArithmeticTemplateError(ValueError):
    """Понятная ошибка при загрузке или генерации арифметического шаблона."""


@dataclass(frozen=True)
class GeneratedArithmeticProblem:
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int | list[int]
    parameters: dict[str, Any]
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "source_problem_numbers": self.source_problem_numbers,
            "problem_text": self.problem_text,
            "answer": self.answer,
            "parameters": self.parameters,
            "seed": self.seed,
        }


def _rand_from_spec(rng: random.Random, spec: dict[str, Any]) -> int:
    if "min_digits" in spec or "max_digits" in spec:
        min_digits = int(spec.get("min_digits", 1))
        max_digits = int(spec.get("max_digits", min_digits))
        digits = rng.randint(min_digits, max_digits)
        low = 10 ** (digits - 1)
        high = 10 ** digits - 1
        return rng.randint(low, high)
    return rng.randint(int(spec["min"]), int(spec["max"]))


def _values_from_specs(template: dict[str, Any], rng: random.Random) -> dict[str, int]:
    return {name: _rand_from_spec(rng, spec) for name, spec in template.get("parameters", {}).items()}


def _render(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise ArithmeticTemplateError(f"Нет значения для плейсхолдера {key}.")
        return str(values[key])

    rendered = PLACEHOLDER_RE.sub(replace, template)
    if "{" in rendered or "}" in rendered:
        raise ArithmeticTemplateError("В условии остались незаполненные плейсхолдеры.")
    return rendered


def _visible_sequence(terms: list[int], *, signs: list[int] | None = None) -> str:
    if len(terms) <= 7:
        visible_indexes = list(range(len(terms)))
    else:
        visible_indexes = [0, 1, 2, 3, -2, -1]

    parts: list[str] = []
    for pos, index in enumerate(visible_indexes):
        if pos == 4 and len(terms) > 7:
            parts.append("+ …")
        term_index = index if index >= 0 else len(terms) + index
        value = terms[term_index]
        sign = signs[term_index] if signs is not None else 1
        if not parts:
            parts.append(str(value) if sign > 0 else f"- {value}")
            continue
        parts.append(("+" if sign > 0 else "-") + f" {value}")
    return " ".join(parts)


def _ap_terms(start: int, step: int, terms: int) -> list[int]:
    return [start + step * index for index in range(terms)]


def _alternating_step_terms(start: int, step_1: int, step_2: int, terms: int) -> list[int]:
    values = [start]
    while len(values) < terms:
        step = step_1 if (len(values) - 1) % 2 == 0 else step_2
        values.append(values[-1] + step)
    return values


def _alternating_pair_terms(start: int, offset: int, period: int, pairs: int, *, positive_tail: bool) -> tuple[list[int], list[int]]:
    terms: list[int] = []
    signs: list[int] = []
    for index in range(pairs):
        plus_term = start + period * index
        terms.extend([plus_term, plus_term + offset])
        signs.extend([1, -1])
    if positive_tail:
        terms.append(start + period * pairs)
        signs.append(1)
    return terms, signs


def _growing_even_gap_terms(start: int, first_gap: int, even_start: int, terms: int) -> list[int]:
    values = [start]
    if terms > 1:
        values.append(start + first_gap)
    gap = even_start
    while len(values) < terms:
        values.append(values[-1] + gap)
        gap += 2
    return values


def _answer_for_terms(terms: list[int], signs: list[int] | None = None) -> int:
    if signs is None:
        return sum(terms)
    return sum(value * sign for value, sign in zip(terms, signs, strict=True))


def _with_sequence(template: dict[str, Any], values: dict[str, Any], terms: list[int], signs: list[int] | None = None) -> GeneratedArithmeticProblem:
    values["sequence"] = _visible_sequence(terms, signs=signs)
    values["terms_full"] = terms
    if signs is not None:
        values["signs_full"] = signs
    return _problem(template, values, _answer_for_terms(terms, signs))


def _problem(template: dict[str, Any], values: dict[str, Any], answer: int | list[int]) -> GeneratedArithmeticProblem:
    return GeneratedArithmeticProblem(
        template_id=str(template["id"]),
        source_problem_numbers=list(template["source_problem_numbers"]),
        problem_text=_render(str(template["render_template"]), values),
        answer=answer,
        parameters=values,
    )


Strategy = Callable[[dict[str, Any], random.Random], GeneratedArithmeticProblem]
STRATEGIES: dict[str, Strategy] = {}


def _strategy(name: str) -> Callable[[Strategy], Strategy]:
    def register(func: Strategy) -> Strategy:
        STRATEGIES[name] = func
        return func
    return register


@_strategy("consecutive_products")
def _consecutive_products(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["base_plus_1"] = v["base"] + 1
    v["base_plus_2"] = v["base"] + 2
    answer = v["base"] * v["coef_1"] + v["base_plus_1"] * v["coef_2"] + v["base_plus_2"] * v["coef_3"]
    return _problem(template, v, answer)


@_strategy("ap_sum_minus")
def _ap_sum_minus(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    terms = _ap_terms(v["start"], v["step"], v["terms"])
    v["sequence"] = _visible_sequence(terms)
    v["terms_full"] = terms
    return _problem(template, v, sum(terms) - v["subtract"])


@_strategy("ap_sum")
@_strategy("ap_sum_visible_four")
@_strategy("large_step_ap_sum")
@_strategy("long_ap_sum")
def _ap_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    terms = _ap_terms(v["start"], v["step"], v["terms"])
    return _with_sequence(template, v, terms)


@_strategy("medium_step_ap_sum")
def _medium_step_ap_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["step"] = 3
    terms = _ap_terms(v["start"], 3, v["terms"])
    return _with_sequence(template, v, terms)


@_strategy("consecutive_integer_sum")
def _consecutive_integer_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["step"] = 1
    terms = _ap_terms(v["start"], 1, v["terms"])
    return _with_sequence(template, v, terms)


@_strategy("odd_step_sum")
def _odd_step_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    if v["start"] % 2 == 0:
        v["start"] += 1
    v["step"] = 2
    return _with_sequence(template, v, _ap_terms(v["start"], 2, v["terms"]))


@_strategy("step_five_ap_sum")
def _step_five_ap_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["step"] = 5
    return _with_sequence(template, v, _ap_terms(v["start"], 5, v["terms"]))


@_strategy("step_six_ap_sum")
def _step_six_ap_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["step"] = 6
    return _with_sequence(template, v, _ap_terms(v["start"], 6, v["terms"]))


@_strategy("alternating_pairs_negative_tail")
@_strategy("alternating_pairs_shifted_negative_tail")
def _alternating_pairs_negative_tail(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    terms, signs = _alternating_pair_terms(v["start"], 1, v["period"], v["pairs"], positive_tail=False)
    return _with_sequence(template, v, terms, signs)


@_strategy("alternating_pairs_positive_tail")
@_strategy("alternating_pairs_shifted_positive_tail")
@_strategy("long_alternating_pairs_positive_tail")
def _alternating_pairs_positive_tail(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    terms, signs = _alternating_pair_terms(v["start"], 1, v["period"], v["pairs"], positive_tail=True)
    return _with_sequence(template, v, terms, signs)


@_strategy("alternating_steps_sum")
@_strategy("alternating_steps_34_sum")
def _alternating_steps_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    terms = _alternating_step_terms(v["start"], v["step_1"], v["step_2"], v["terms"])
    return _with_sequence(template, v, terms)


@_strategy("growing_even_gaps_sum")
def _growing_even_gaps_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["first_gap"] = 1
    if v["even_start"] % 2:
        v["even_start"] += 1
    terms = _growing_even_gap_terms(v["start"], v["first_gap"], v["even_start"], v["terms"])
    return _with_sequence(template, v, terms)


@_strategy("paired_near_products")
def _paired_near_products(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["round_low"] = v["round_high"] - 4
    v["left_factor_plus_2"] = v["left_factor"] + 2
    v["right_factor_minus_4"] = max(2, v["right_factor"] - 4)
    answer = v["round_high"] + v["left_factor"] * v["right_factor"] - v["round_low"] + v["left_factor_plus_2"] * v["right_factor_minus_4"]
    return _problem(template, v, answer)


@_strategy("triple_and_neighbor_cancellation")
def _triple_and_neighbor_cancellation(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["triple_base"] = v["base"] * 3
    v["inner_times_3_minus_1"] = v["inner"] * 3 - 1
    v["x_minus_1"] = v["x"] - 1
    v["y_minus_1"] = v["y"] - 1
    answer = v["triple_base"] * 3 * v["inner"] - v["base"] * 3 * v["inner_times_3_minus_1"] + v["x"] * v["y"] - v["x_minus_1"] * v["y_minus_1"]
    return _problem(template, v, answer)


@_strategy("three_neighbor_products")
@_strategy("three_shifted_neighbor_products")
def _three_neighbor_products(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["n_minus_1"] = v["n"] - 1
    v["n_plus_1"] = v["n"] + 1
    v["n_plus_2"] = v["n"] + 2
    v["tail"] = v["n"] - v["tail_shift"]
    if template["generation_strategy"] == "three_neighbor_products":
        answer = v["n_minus_1"] * v["n"] + v["n"] * v["n_plus_1"] + v["n_plus_1"] * v["tail"]
    else:
        answer = v["n_minus_1"] * v["n"] + v["n"] * v["n_plus_2"] + v["n_plus_1"] * v["tail"]
    return _problem(template, v, answer)


@_strategy("large_times_small")
def _large_times_small(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    return _problem(template, v, v["large_factor"] * v["small_factor"])


@_strategy("common_factor_two_plus_complement")
def _common_factor_two_plus_complement(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["part_2"] = rng.randint(20, 300)
    v["total_parts"] = v["part_1"] + v["part_2"]
    if v["round_base"] <= v["common"]:
        v["round_base"] = v["common"] + rng.randint(50, 250)
    v["complement"] = v["round_base"] - v["common"]
    answer = v["common"] * v["part_1"] + v["common"] * v["part_2"] + v["complement"] * v["total_parts"]
    return _problem(template, v, answer)


@_strategy("distributed_common_factor")
def _distributed_common_factor(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    common = rng.randint(2, 12)
    v: dict[str, Any] = {"common_factor": common}
    for term in range(1, 4):
        v[f"a{term}"] = rng.randint(5, 29)
        v[f"b{term}"] = common * rng.randint(2, 9)
        v[f"c{term}"] = rng.randint(4, 25)
        v[f"term_{term}"] = v[f"a{term}"] * v[f"b{term}"] * v[f"c{term}"]
    if math.gcd(v["term_1"], v["term_2"], v["term_3"]) <= 1:
        raise ArithmeticTemplateError("Не удалось сохранить общий множитель.")
    return _problem(template, v, v["term_1"] + v["term_2"] + v["term_3"])


@_strategy("grouped_common_factor_expression")
def _grouped_common_factor_expression(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["c"] = v["round_total"] - v["a"] + 1
    if v["c"] <= 0:
        v["a"] = rng.randint(20, v["round_total"] - 5)
        v["c"] = v["round_total"] - v["a"] + 1
    answer = v["a"] * v["common"] - v["common"] - v["b"] * v["round_total"] + v["common"] * v["c"]
    return _problem(template, v, answer)


@_strategy("factorial")
def _factorial(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    return _problem(template, v, math.factorial(v["n"]))


@_strategy("three_distributive_subproblems")
def _three_distributive_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    a = rng.randint(4, 15)
    b = rng.randint(20, 70)
    c = rng.randint(20, 70)
    e = rng.randint(4, 12)
    d = rng.randint(25, 70)
    f = rng.randint(5, d - 4)
    h = rng.randint(20, 60)
    k = rng.randint(30, 80)
    g, i, j = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
    v = {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f, "g": g, "h": h, "i": i, "j": j, "k": k}
    return _problem(template, v, [a * b + a * c, d * e - e * f, g * h + i * h + j * k])


@_strategy("two_common_factor_subproblems")
def _two_common_factor_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    v["c"] = v["d"] + rng.randint(20, 140)
    return _problem(
        template,
        v,
        [v["a"] * v["common"] + v["b"] * v["common"], v["c"] * v["common"] - v["d"] * v["common"]],
    )


@_strategy("single_common_factor_sum")
def _single_common_factor_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    return _problem(template, v, v["a"] * v["common"] + v["b"] * v["common"])


def _distributed_terms(prefixes: tuple[str, str, str], common: int, rng: random.Random) -> dict[str, int]:
    values: dict[str, int] = {}
    for prefix in prefixes:
        values[f"{prefix}1"] = rng.randint(5, 29)
        values[f"{prefix}2"] = common * rng.randint(2, 9)
        values[f"{prefix}3"] = rng.randint(4, 25)
    return values


@_strategy("two_distributed_common_factor_subproblems")
def _two_distributed_common_factor_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    common_a = rng.randint(2, 12)
    common_b = rng.randint(2, 12)
    v: dict[str, Any] = {"common_factor_a": common_a, "common_factor_b": common_b}
    v.update(_distributed_terms(("a", "b", "c"), common_a, rng))
    v.update(_distributed_terms(("d", "e", "f"), common_b, rng))
    v["term_a_1"] = v["a1"] * v["b1"] * v["c1"]
    v["term_a_2"] = v["a2"] * v["b2"] * v["c2"]
    v["term_a_3"] = v["a3"] * v["b3"] * v["c3"]
    v["term_b_1"] = v["d1"] * v["e1"] * v["f1"]
    v["term_b_2"] = v["d2"] * v["e2"] * v["f2"]
    v["term_b_3"] = v["d3"] * v["e3"] * v["f3"]
    return _problem(
        template,
        v,
        [v["term_a_1"] + v["term_a_2"] + v["term_a_3"], v["term_b_1"] + v["term_b_2"] + v["term_b_3"]],
    )


@_strategy("multi_ap_subproblems")
def _multi_ap_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    seq_a = _ap_terms(1, 1, v["terms_a"])
    seq_b = _ap_terms(1, 1, v["terms_b"])
    seq_c = _ap_terms(v["start_c"], 1, v["terms_c"])
    seq_d = _ap_terms(1, 2, v["terms_d"])
    v.update({"seq_a": _visible_sequence(seq_a), "seq_b": _visible_sequence(seq_b), "seq_c": _visible_sequence(seq_c), "seq_d": _visible_sequence(seq_d)})
    return _problem(template, v, [sum(seq_a), sum(seq_b), sum(seq_c), sum(seq_d)])


@_strategy("paired_positive_and_alternating_sum")
def _paired_positive_and_alternating_sum(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    terms = _alternating_step_terms(v["start"], v["step_1"], v["step_2"], v["terms"])
    signs = [1 if index % 2 == 0 else -1 for index in range(len(terms))]
    v["seq_positive"] = _visible_sequence(terms)
    v["seq_alternating"] = _visible_sequence(terms, signs=signs)
    v["terms_full"] = terms
    v["signs_full"] = signs
    return _problem(template, v, [sum(terms), _answer_for_terms(terms, signs)])


@_strategy("mixed_ap_and_alternating_subproblems")
def _mixed_ap_and_alternating_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    if v["terms_c"] % 2 == 0:
        v["terms_c"] += 1
    seq_a = _ap_terms(v["start_a"], v["step_a"], v["terms_a"])
    seq_b = _ap_terms(v["start_b"], v["step_b"], v["terms_b"])
    seq_c = _ap_terms(1, 2, v["terms_c"])
    signs_c = [1 if index % 2 == 0 else -1 for index in range(len(seq_c))]
    v.update({"seq_a": _visible_sequence(seq_a), "seq_b": _visible_sequence(seq_b), "seq_c": _visible_sequence(seq_c, signs=signs_c)})
    return _problem(template, v, [sum(seq_a), sum(seq_b), _answer_for_terms(seq_c, signs_c)])


@_strategy("ap_and_alternating_subproblems")
def _ap_and_alternating_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    if v["terms_b"] % 2 == 0:
        v["terms_b"] += 1
    seq_a = _ap_terms(v["start_a"], v["step_a"], v["terms_a"])
    seq_b = _ap_terms(1, 3, v["terms_b"])
    signs_b = [1 if index % 2 == 0 else -1 for index in range(len(seq_b))]
    v.update({"seq_a": _visible_sequence(seq_a), "seq_b": _visible_sequence(seq_b, signs=signs_b)})
    return _problem(template, v, [sum(seq_a), _answer_for_terms(seq_b, signs_b)])


@_strategy("two_ap_subproblems")
def _two_ap_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    v = _values_from_specs(template, rng)
    seq_a = _ap_terms(1, 1, v["terms_a"])
    seq_b = _ap_terms(1, 3, v["terms_b"])
    v.update({"seq_a": _visible_sequence(seq_a), "seq_b": _visible_sequence(seq_b)})
    return _problem(template, v, [sum(seq_a), sum(seq_b)])


@_strategy("two_grouping_subproblems")
def _two_grouping_subproblems(template: dict[str, Any], rng: random.Random) -> GeneratedArithmeticProblem:
    c = rng.randint(8, 40)
    b = rng.randint(30, 90)
    a = c * 2 + rng.randint(3, 9)
    d, e = rng.randint(4, 15), rng.randint(12, 40)
    f, g = rng.randint(2, 9), rng.randint(12, 40)
    h, i = rng.randint(2, 9), rng.randint(30, 80)
    v = {"a": a, "b": b, "b_minus_1": b - 1, "c": c, "d": d, "e": e, "f": f, "g": g, "h": h, "i": i}
    return _problem(template, v, [a * b - (b - 1) * c, d * e + f * g + h * i])


@lru_cache(maxsize=4)
def _load_payload(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_arithmetic_templates(path: str | Path = DEFAULT_ARITHMETIC_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    if not resolved.exists() and Path(path) == DEFAULT_ARITHMETIC_TEMPLATE_PATH and LEGACY_ARITHMETIC_TEMPLATE_PATH.exists():
        resolved = LEGACY_ARITHMETIC_TEMPLATE_PATH.resolve()
    payload = _load_payload(str(resolved), resolved.stat().st_mtime_ns)
    templates = payload.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ArithmeticTemplateError("В arithmetic problem set нет списка templates.")
    validate_arithmetic_catalog(templates)
    return list(templates)


def validate_arithmetic_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    seen_numbers: list[int] = []
    for template in templates:
        for field in ("id", "title", "source_problem_numbers", "render_template", "parameters", "generation_strategy", "answer_strategy"):
            if field not in template:
                raise ArithmeticTemplateError(f"У шаблона нет поля {field}: {template!r}")
        template_id = str(template["id"])
        if template_id in ids:
            raise ArithmeticTemplateError(f"Повторяющийся id шаблона: {template_id}")
        ids.add(template_id)
        if template["generation_strategy"] not in STRATEGIES:
            raise ArithmeticTemplateError(f"Нет стратегии {template['generation_strategy']} для {template_id}.")
        numbers = template["source_problem_numbers"]
        if not isinstance(numbers, list) or not all(isinstance(item, int) for item in numbers):
            raise ArithmeticTemplateError(f"Некорректные source_problem_numbers у {template_id}.")
        seen_numbers.extend(numbers)

    if set(seen_numbers) != SOURCE_PROBLEM_NUMBERS:
        missing = sorted(SOURCE_PROBLEM_NUMBERS - set(seen_numbers))
        extra = sorted(set(seen_numbers) - SOURCE_PROBLEM_NUMBERS)
        raise ArithmeticTemplateError(f"Проблема покрытия источника. missing={missing}, extra={extra}")
    duplicates = sorted(number for number in set(seen_numbers) if seen_numbers.count(number) > 1)
    if duplicates:
        raise ArithmeticTemplateError(f"Номера источника встречаются дважды: {duplicates}")


def arithmetic_template_metadata() -> dict[str, Any]:
    templates = load_arithmetic_templates()
    module = {
        "module_id": "arithmetic",
        "title": "arithmetic",
        "display_name": "arithmetic",
        "template_count": len(templates),
        "covered_source_problem_numbers": len(SOURCE_PROBLEM_NUMBERS),
    }
    return {
        "modules": [module],
        "templates": [
            {
                "template_id": template["id"],
                "title": template["title"],
                "display_name": f"{template['title']} — источники: {', '.join(map(str, template['source_problem_numbers']))}",
                "module_name": "Арифметические вычисления",
                "source_problem_numbers": template["source_problem_numbers"],
                "difficulty": template.get("difficulty", "medium"),
                "generation_strategy": template["generation_strategy"],
            }
            for template in templates
        ],
        "stats": {
            "total_modules": 1,
            "total_templates": len(templates),
            "covered_source_problem_numbers": len(SOURCE_PROBLEM_NUMBERS),
            "source_file": "docs/01_arifmeticheskie_vychisleniya_updated.md",
        },
    }


def get_arithmetic_template(template_id: str) -> dict[str, Any]:
    for template in load_arithmetic_templates():
        if template["id"] == template_id:
            return template
    raise ArithmeticTemplateError(f"Неизвестный арифметический шаблон: {template_id}.")


def generate_arithmetic_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedArithmeticProblem:
    template = get_arithmetic_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    last_error: Exception | None = None
    for _ in range(MAX_ATTEMPTS):
        try:
            generated = STRATEGIES[template["generation_strategy"]](template, local_rng)
            if generated.problem_text in set(template.get("source_examples", [])):
                continue
            validate_generated_problem(generated)
            return GeneratedArithmeticProblem(
                template_id=generated.template_id,
                source_problem_numbers=generated.source_problem_numbers,
                problem_text=generated.problem_text,
                answer=generated.answer,
                parameters=generated.parameters,
                seed=seed,
            )
        except Exception as error:  # noqa: BLE001 - retries produce a clear final error.
            last_error = error
    raise ArithmeticTemplateError(f"Не удалось сгенерировать {template_id}: {last_error}")


def generate_arithmetic_worksheet(template_ids: list[str], *, seed: int | None = None) -> dict[str, Any]:
    if len(template_ids) != 5:
        raise ArithmeticTemplateError("Выберите ровно пять шаблонов.")
    if len(set(template_ids)) != 5:
        raise ArithmeticTemplateError("Один и тот же шаблон нельзя выбрать дважды.")
    rng = random.Random(seed if seed is not None else datetime.now().timestamp())
    problems = [
        generate_arithmetic_problem(template_id, rng=rng).to_dict() | {"position": index}
        for index, template_id in enumerate(template_ids, start=1)
    ]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": datetime.now().strftime("%d.%m.%Y"),
        "selected_templates": [
            {
                "template_id": problem["template_id"],
                "source_problem_numbers": problem["source_problem_numbers"],
                "rendered_problem": problem["problem_text"],
                "answer": problem["answer"],
                "generated_values": problem["parameters"],
                "position": problem["position"],
            }
            for problem in problems
        ],
    }


def generate_arithmetic_worksheet_by_modules(module_ids: list[str], *, seed: int | None = None) -> dict[str, Any]:
    if len(module_ids) != 5:
        raise ArithmeticTemplateError("Выберите ровно пять модулей.")
    unknown = sorted({module_id for module_id in module_ids if module_id != "arithmetic"})
    if unknown:
        raise ArithmeticTemplateError(f"Неизвестный модуль: {', '.join(unknown)}.")

    templates = load_arithmetic_templates()
    rng = random.Random(seed if seed is not None else datetime.now().timestamp())
    problems = []
    for index, module_id in enumerate(module_ids, start=1):
        template = rng.choice(templates)
        generated = generate_arithmetic_problem(str(template["id"]), rng=rng).to_dict()
        generated["position"] = index
        generated["module_id"] = module_id
        problems.append(generated)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": datetime.now().strftime("%d.%m.%Y"),
        "selected_modules": list(module_ids),
        "selected_templates": [
            {
                "module_id": problem["module_id"],
                "template_id": problem["template_id"],
                "source_problem_numbers": problem["source_problem_numbers"],
                "rendered_problem": problem["problem_text"],
                "answer": problem["answer"],
                "generated_values": problem["parameters"],
                "position": problem["position"],
            }
            for problem in problems
        ],
    }


def validate_generated_problem(problem: GeneratedArithmeticProblem) -> None:
    if not problem.problem_text.strip():
        raise ArithmeticTemplateError("Пустой текст задачи.")
    if "{" in problem.problem_text or "}" in problem.problem_text:
        raise ArithmeticTemplateError(f"Незаполненные плейсхолдеры в {problem.template_id}.")
    if not isinstance(problem.answer, int) and not (
        isinstance(problem.answer, list) and all(isinstance(item, int) for item in problem.answer)
    ):
        raise ArithmeticTemplateError(f"Ответ должен быть целым числом или списком целых чисел: {problem.template_id}.")
    if problem.template_id == "arithmetic_019":
        values = problem.parameters
        common = math.gcd(int(values["term_1"]), int(values["term_2"]), int(values["term_3"]))
        if common <= 1:
            raise ArithmeticTemplateError("У задачи на общий множитель нет нетривиального общего делителя.")
    if problem.template_id == "arithmetic_036":
        values = problem.parameters
        common_a = math.gcd(int(values["term_a_1"]), int(values["term_a_2"]), int(values["term_a_3"]))
        common_b = math.gcd(int(values["term_b_1"]), int(values["term_b_2"]), int(values["term_b_3"]))
        if common_a <= 1 or common_b <= 1:
            raise ArithmeticTemplateError("В одном из подпунктов нет нетривиального общего делителя.")
    if "terms_full" in problem.parameters:
        terms = problem.parameters["terms_full"]
        if not isinstance(terms, list) or len(terms) < 2:
            raise ArithmeticTemplateError("Последовательность должна содержать минимум два члена.")
