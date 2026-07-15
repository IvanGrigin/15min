from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "docs" / "02_uravneniya_i_neravenstva_without_1502.md"
OUTPUT_DIR = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "equations"
OUTPUT_PATH = OUTPUT_DIR / "templates.json"

NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
INTEGER_RE = re.compile(r"^-?\d+$")


def _read_source() -> list[tuple[int, str]]:
    problems: list[tuple[int, str]] = []
    for line in SOURCE_PATH.read_text(encoding="utf-8").splitlines():
        match = NUMBERED_LINE_RE.match(line)
        if match:
            problems.append((int(match.group(1)), match.group(2).strip()))
    return problems


def _clean_expression(text: str) -> str:
    return text.strip().rstrip(".").strip()


def _split_single_equation(text: str) -> tuple[str, str, str] | None:
    if "неравенства" in text or "систем" in text or re.search(r"(^|\s)[аa]\)", text):
        return None
    if "=" not in text:
        return None
    before_equal = text.split("=", 1)[0]
    first_colon = before_equal.find(":")
    if first_colon != -1 and not re.search(r"\d", before_equal[:first_colon]):
        prefix, equation = text.split(":", 1)
    elif " равенства " in before_equal:
        prefix, equation_start = text.split(" равенства ", 1)
        prefix = f"{prefix} равенства"
        equation = equation_start
    elif " уравнении " in before_equal:
        prefix, equation_start = text.split(" уравнении ", 1)
        prefix = f"{prefix} уравнении"
        equation = equation_start
    else:
        prefix, equation = "Найдите значение x", text
    left, right = equation.split("=", 1)
    left = _clean_expression(left)
    right = _clean_expression(right)
    if re.search(r"(^|\s)1\)", left):
        left = _clean_expression(re.split(r"(^|\s)1\)", left, maxsplit=1)[-1])
    if ". " in left:
        left = _clean_expression(left.rsplit(". ", 1)[1])
    if "x" in left and INTEGER_RE.fullmatch(right):
        return prefix.strip(), left, "right"
    if "x" in right and INTEGER_RE.fullmatch(left):
        return prefix.strip(), right, "left"
    fallback = re.search(r"(.+?)=\s*(-?\d+)\.?$", text)
    if fallback and "x" in fallback.group(1):
        left_side = _clean_expression(fallback.group(1))
        if ":" in left_side and not re.search(r"\d", left_side.split(":", 1)[0]):
            prefix_text, left_side = left_side.split(":", 1)
            prefix = prefix_text.strip()
        if re.search(r"(^|\s)1\)", left_side):
            left_side = _clean_expression(re.split(r"(^|\s)1\)", left_side, maxsplit=1)[-1])
        if ". " in left_side:
            left_side = _clean_expression(left_side.rsplit(". ", 1)[1])
        return prefix.strip(), left_side, "right"
    return None


def _single_template(number: int, text: str, index: int) -> dict[str, object]:
    parsed = _split_single_equation(text)
    if parsed is None:
        raise ValueError(f"Не удалось разобрать одиночное уравнение {number}: {text}")
    prefix, x_expression, result_side = parsed
    if result_side == "right":
        render_template = f"{prefix}: {x_expression} = {{result}}."
    else:
        render_template = f"{prefix}: {{result}} = {x_expression}."
    return {
        "id": f"equation_{index:03d}",
        "title": f"Уравнение по задаче {number}",
        "module_id": "equations",
        "problem_type": "single_equation",
        "generation_strategy": "single_equation_from_integer_solution",
        "source_problem_numbers": [number],
        "source_text": text,
        "render_template": render_template,
        "x_expression": x_expression,
        "result_side": result_side,
        "answer_definition": "Целое значение x, при котором левая и правая части уравнения равны.",
    }


def _manual_templates(source_by_number: dict[int, str], start_index: int) -> list[dict[str, object]]:
    templates: list[dict[str, object]] = []

    templates.append({
        "id": f"equation_{start_index:03d}",
        "title": "Наибольшее натуральное решение неравенства, тип 1",
        "module_id": "equations",
        "problem_type": "inequality",
        "generation_strategy": "inequality_greatest_natural",
        "inequality_variant": "difference_product",
        "source_problem_numbers": [1173, 1373],
        "source_text": " / ".join(source_by_number[number] for number in (1173, 1373)),
        "render_template": "Найти наибольшее натуральное решение неравенства: x ≤ ({a} - {b}) · {c}: ({d} + {e}:{f}).",
        "answer_definition": "Наибольшее натуральное число x, удовлетворяющее неравенству.",
    })
    start_index += 1

    templates.append({
        "id": f"equation_{start_index:03d}",
        "title": "Наибольшее натуральное решение неравенства, тип 2",
        "module_id": "equations",
        "problem_type": "inequality",
        "generation_strategy": "inequality_greatest_natural",
        "inequality_variant": "sum_difference_product",
        "source_problem_numbers": [1195, 1395],
        "source_text": " / ".join(source_by_number[number] for number in (1195, 1395)),
        "render_template": "Найти наибольшее натуральное решение неравенства: x ≤ ({a} - {b} + {c}) · {d}: ({e} - {f} / {g}).",
        "answer_definition": "Наибольшее натуральное число x, удовлетворяющее неравенству.",
    })
    start_index += 1

    templates.append({
        "id": f"equation_{start_index:03d}",
        "title": "Две системы линейных уравнений, тип 1",
        "module_id": "equations",
        "problem_type": "linear_systems",
        "generation_strategy": "two_linear_systems",
        "system_count": 2,
        "source_problem_numbers": [1203, 1403],
        "source_text": " / ".join(source_by_number[number] for number in (1203, 1403)),
        "render_template": "Решите системы уравнений: а) {a11}x + {b11}y = {c11}, {a12}x + {b12}y = {c12}; б) {a21}x + {b21}y = {c21}, {a22}x + {b22}y = {c22}.",
        "answer_definition": "Для каждой системы нужно найти целую пару (x, y).",
    })
    start_index += 1

    templates.append({
        "id": f"equation_{start_index:03d}",
        "title": "Две системы линейных уравнений, тип 2",
        "module_id": "equations",
        "problem_type": "linear_systems",
        "generation_strategy": "two_linear_systems",
        "system_count": 2,
        "source_problem_numbers": [1223, 1423],
        "source_text": " / ".join(source_by_number[number] for number in (1223, 1423)),
        "render_template": "Решите системы уравнений: а) {a11}x + {b11}y = {c11} и {a12}x + {b12}y = {c12}. б) {a21}x + {b21}y = {c21} и {a22}x + {b22}y = {c22}.",
        "answer_definition": "Для каждой системы нужно найти целую пару (x, y).",
    })
    start_index += 1

    templates.append({
        "id": f"equation_{start_index:03d}",
        "title": "Три уравнения в одном задании",
        "module_id": "equations",
        "problem_type": "multipart_equations",
        "generation_strategy": "multipart_equations",
        "source_problem_numbers": [1232, 1432],
        "source_text": " / ".join(source_by_number[number] for number in (1232, 1432)),
        "render_template": "Найдите x: а) {part_а}; б) {part_б}; в) {part_в}.",
        "parts": [
            {
                "label": "а",
                "x_expression": "(13 * x - 1245) / 6 - 155",
                "result_side": "right",
                "render_template": "(13 × x - 1245) / 6 - 155 = {result}",
            },
            {
                "label": "б",
                "x_expression": "(6363 + 324 * x) / 25 - 167",
                "result_side": "right",
                "render_template": "(6363 + 324 × x) / 25 - 167 = {result}",
            },
            {
                "label": "в",
                "x_expression": "((191 - (259 - x)) * 98 + 270) / 2",
                "result_side": "left",
                "render_template": "{result} = ((191 - (259 - x)) × 98 + 270): 2",
            },
        ],
        "answer_definition": "Нужно найти три целых значения x: отдельно для пунктов а, б и в.",
    })

    return templates


def build_catalog() -> dict[str, object]:
    source = _read_source()
    source_by_number = dict(source)
    manual_numbers = {1173, 1195, 1203, 1223, 1232, 1373, 1395, 1403, 1423, 1432}
    templates: list[dict[str, object]] = []
    index = 1
    for number, text in source:
        if number in manual_numbers:
            continue
        templates.append(_single_template(number, text, index))
        index += 1
    templates.extend(_manual_templates(source_by_number, index))
    covered = [number for template in templates for number in template["source_problem_numbers"]]
    if sorted(covered) != sorted(source_by_number):
        raise RuntimeError("Покрытие источника не совпало с исходным файлом.")
    if len(covered) != len(set(covered)):
        raise RuntimeError("Некоторые исходные номера попали в шаблоны дважды.")
    return {
        "schema_version": 1,
        "module": {
            "id": "equations",
            "title": "Equations",
            "source_file": "docs/02_uravneniya_i_neravenstva_without_1502.md",
            "description": "Шаблоны уравнений, неравенств и систем, построенные по исходному файлу с задачами.",
        },
        "source_accounting": {
            "source_problem_count": len(source),
            "template_count": len(templates),
            "excluded_problem_numbers": [1502],
            "covered_problem_numbers": sorted(source_by_number),
        },
        "templates": templates,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_catalog()
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(payload['templates'])} equation templates to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
