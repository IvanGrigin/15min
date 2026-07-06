#!/usr/bin/env python3
"""
Генератор математических задач с шаблонами и экспортом в JSON.

Что умеет программа:
1. Хранит несколько шаблонов задач.
2. Позволяет задавать диапазоны чисел в каждом шаблоне.
3. Фильтрует задачи по сложности промежуточных вычислений.
4. Сохраняет условие, ответ и метаинформацию в JSON-файл.

Пример запуска:
python3 01.py --count 3 --output generated_problems.json

Пример запуска с ограничением сложности:
python3 01.py --count 5 --min-level однозначное --max-level двузначное

Пример переопределения диапазонов:
python3 01.py --set-range segment_on_line.ab=10:20 --set-range rectangle_perimeter.a=3:8
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Sequence


# Числовые уровни сложности по количеству цифр.
DIGIT_LABELS = {
    1: "однозначное",
    2: "двузначное",
    3: "трехзначное",
    4: "многозначное",
}

# Алиасы нужны, чтобы можно было писать параметры по-русски в разных вариантах.
DIGIT_ALIASES = {
    "1": 1,
    "однозначное": 1,
    "однозначный": 1,
    "2": 2,
    "двузначное": 2,
    "двузначный": 2,
    "3": 3,
    "трехзначное": 3,
    "трёхзначное": 3,
    "трехзначный": 3,
    "трёхзначный": 3,
    "4": 4,
    "многозначное": 4,
    "многозначный": 4,
}


@dataclass(frozen=True)
class NumberRange:
    """Диапазон целых чисел включительно."""

    min_value: int
    max_value: int

    def sample(self, rng: random.Random) -> int:
        return rng.randint(self.min_value, self.max_value)

    def to_dict(self) -> Dict[str, int]:
        return {"min": self.min_value, "max": self.max_value}


@dataclass(frozen=True)
class ProblemTemplate:
    """Описание шаблона задачи."""

    code: str
    name: str
    category: str
    problem_type: str
    parameter_ranges: Dict[str, NumberRange]
    builder: Callable[[Dict[str, int]], Dict[str, object]]


def number_digit_level(number: int) -> int:
    """
    Возвращает уровень сложности по числу цифр.
    1 -> однозначное, 2 -> двузначное, 3 -> трехзначное, 4 -> многозначное.
    """

    digit_count = len(str(abs(number)))
    return min(digit_count, 4)


def digit_level_label(level: int) -> str:
    """Возвращает текстовую подпись уровня сложности."""

    return DIGIT_LABELS.get(level, "неизвестно")


def parse_digit_level(value: str) -> int:
    """Преобразует текстовый уровень сложности в число."""

    normalized = value.strip().lower()
    if normalized not in DIGIT_ALIASES:
        supported = ", ".join(sorted(DIGIT_ALIASES))
        raise argparse.ArgumentTypeError(
            f"Неизвестный уровень сложности '{value}'. Допустимые значения: {supported}"
        )
    return DIGIT_ALIASES[normalized]


def choose_word_form(number: int, forms: Sequence[str]) -> str:
    """
    Выбирает правильную форму слова для русского языка.
    Пример: 1 задача, 2 задачи, 5 задач.
    """

    last_two = number % 100
    last_one = number % 10

    if 11 <= last_two <= 14:
        return forms[2]
    if last_one == 1:
        return forms[0]
    if 2 <= last_one <= 4:
        return forms[1]
    return forms[2]


def format_counted_noun(number: int, forms: Sequence[str]) -> str:
    """Возвращает строку вида '5 задач' или '4 задачи'."""

    return f"{number} {choose_word_form(number, forms)}"


def parse_range_override(raw_value: str) -> tuple[str, str, NumberRange]:
    """
    Разбирает строку вида template.parameter=MIN:MAX.
    Пример: segment_on_line.ab=10:20
    """

    try:
        left_part, right_part = raw_value.split("=", 1)
        template_code, parameter_name = left_part.split(".", 1)
        min_text, max_text = right_part.split(":", 1)
        range_value = NumberRange(int(min_text), int(max_text))
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Параметр --set-range должен иметь вид template.parameter=MIN:MAX"
        ) from error

    if range_value.min_value > range_value.max_value:
        raise argparse.ArgumentTypeError("В диапазоне MIN не может быть больше MAX")

    return template_code, parameter_name, range_value


def build_segment_on_line(params: Dict[str, int]) -> Dict[str, object]:
    """Шаблон про длины отрезков на прямой."""

    ab = params["ab"]
    bc = params["bc"]
    diff_value = abs(ab - bc)
    sum_value = ab + bc

    return {
        "problem": (
            f"На прямой отмечены два отрезка AB и BC с длинами {ab} и {bc} соответственно. "
            "Какой может быть длина отрезка AC?"
        ),
        "answer": sorted({diff_value, sum_value}),
        "intermediate_values": [diff_value, sum_value],
        "explanation": (
            "Точка B может лежать между A и C, тогда AC = AB + BC, "
            "или точка A либо C может лежать между двумя другими точками, тогда AC = |AB - BC|."
        ),
    }


def build_rectangle_perimeter(params: Dict[str, int]) -> Dict[str, object]:
    """Шаблон на периметр прямоугольника."""

    a = params["a"]
    b = params["b"]
    half_perimeter = a + b
    perimeter = 2 * half_perimeter

    return {
        "problem": (
            f"Длина прямоугольника равна {a} см, а ширина равна {b} см. "
            "Найдите его периметр."
        ),
        "answer": perimeter,
        "intermediate_values": [half_perimeter, perimeter],
        "explanation": "Периметр прямоугольника вычисляется по формуле P = 2 x (a + b).",
    }


def build_notebooks_cost(params: Dict[str, int]) -> Dict[str, object]:
    """Шаблон на стоимость покупки."""

    price = params["price"]
    notebooks = params["notebooks"]
    pens = params["pens"]
    pen_price = params["pen_price"]

    notebooks_cost = price * notebooks
    pens_cost = pen_price * pens
    total_cost = notebooks_cost + pens_cost

    return {
        "problem": (
            f"Одна тетрадь стоит {format_counted_noun(price, ('рубль', 'рубля', 'рублей'))}, "
            f"а одна ручка стоит {format_counted_noun(pen_price, ('рубль', 'рубля', 'рублей'))}. "
            f"Купили {format_counted_noun(notebooks, ('тетрадь', 'тетради', 'тетрадей'))} "
            f"и {format_counted_noun(pens, ('ручка', 'ручки', 'ручек'))}. "
            "Сколько рублей заплатили за всю покупку?"
        ),
        "answer": total_cost,
        "intermediate_values": [notebooks_cost, pens_cost, total_cost],
        "explanation": "Сначала нужно найти стоимость тетрадей и ручек отдельно, затем сложить результаты.",
    }


def build_motion_problem(params: Dict[str, int]) -> Dict[str, object]:
    """Шаблон на движение с целыми ответами."""

    speed = params["speed"]
    hours = params["hours"]
    rest = params["rest"]

    travel_distance = speed * hours
    full_distance = travel_distance + rest

    return {
        "problem": (
            f"Турист шел со скоростью {speed} км/ч в течение "
            f"{format_counted_noun(hours, ('час', 'часа', 'часов'))}, "
            f"а затем проехал еще {rest} км на автобусе. Какое расстояние он преодолел всего?"
        ),
        "answer": full_distance,
        "intermediate_values": [travel_distance, full_distance],
        "explanation": "Сначала находим путь пешком: скорость умножаем на время. Затем прибавляем путь на автобусе.",
    }


def create_templates() -> Dict[str, ProblemTemplate]:
    """Создает набор доступных шаблонов задач."""

    return {
        "segment_on_line": ProblemTemplate(
            code="segment_on_line",
            name="Отрезки на прямой",
            category="геометрия",
            problem_type="отрезки",
            parameter_ranges={
                "ab": NumberRange(5, 40),
                "bc": NumberRange(2, 25),
            },
            builder=build_segment_on_line,
        ),
        "rectangle_perimeter": ProblemTemplate(
            code="rectangle_perimeter",
            name="Периметр прямоугольника",
            category="геометрия",
            problem_type="периметр",
            parameter_ranges={
                "a": NumberRange(2, 35),
                "b": NumberRange(2, 35),
            },
            builder=build_rectangle_perimeter,
        ),
        "notebooks_cost": ProblemTemplate(
            code="notebooks_cost",
            name="Стоимость покупки",
            category="арифметика",
            problem_type="стоимость",
            parameter_ranges={
                "price": NumberRange(4, 30),
                "notebooks": NumberRange(2, 9),
                "pens": NumberRange(2, 8),
                "pen_price": NumberRange(3, 20),
            },
            builder=build_notebooks_cost,
        ),
        "motion_problem": ProblemTemplate(
            code="motion_problem",
            name="Путь туриста",
            category="арифметика",
            problem_type="движение",
            parameter_ranges={
                "speed": NumberRange(3, 18),
                "hours": NumberRange(2, 8),
                "rest": NumberRange(5, 60),
            },
            builder=build_motion_problem,
        ),
    }


def apply_range_overrides(
    templates: Dict[str, ProblemTemplate],
    overrides: Sequence[tuple[str, str, NumberRange]],
) -> Dict[str, ProblemTemplate]:
    """Возвращает копию шаблонов с обновленными диапазонами."""

    updated_templates = dict(templates)

    for template_code, parameter_name, range_value in overrides:
        if template_code not in updated_templates:
            raise ValueError(f"Шаблон '{template_code}' не найден")

        template = updated_templates[template_code]
        if parameter_name not in template.parameter_ranges:
            raise ValueError(
                f"Параметр '{parameter_name}' не найден в шаблоне '{template_code}'"
            )

        new_ranges = dict(template.parameter_ranges)
        new_ranges[parameter_name] = range_value
        updated_templates[template_code] = ProblemTemplate(
            code=template.code,
            name=template.name,
            category=template.category,
            problem_type=template.problem_type,
            parameter_ranges=new_ranges,
            builder=template.builder,
        )

    return updated_templates


def build_problem_metadata(
    template: ProblemTemplate,
    task_number: int,
    payload: Dict[str, object],
    params: Dict[str, int],
    requested_min_level: int,
    requested_max_level: int,
) -> Dict[str, object]:
    """Собирает полную запись задачи для JSON."""

    intermediate_values = list(payload["intermediate_values"])
    actual_min_level = min(number_digit_level(value) for value in intermediate_values)
    actual_max_level = max(number_digit_level(value) for value in intermediate_values)

    return {
        "problem_code": f"{template.code}-{task_number:03d}",
        "template_code": template.code,
        "template_name": template.name,
        "category": template.category,
        "problem_type": template.problem_type,
        "problem": payload["problem"],
        "answer": payload["answer"],
        "parameters": params,
        "parameter_ranges": {
            name: range_value.to_dict()
            for name, range_value in template.parameter_ranges.items()
        },
        "intermediate_values": intermediate_values,
        "difficulty": {
            "requested_min_level": requested_min_level,
            "requested_max_level": requested_max_level,
            "requested_min_label": digit_level_label(requested_min_level),
            "requested_max_label": digit_level_label(requested_max_level),
            "actual_min_level": actual_min_level,
            "actual_max_level": actual_max_level,
            "actual_min_label": digit_level_label(actual_min_level),
            "actual_max_label": digit_level_label(actual_max_level),
        },
        "explanation": payload["explanation"],
    }


def matches_difficulty(
    intermediate_values: Sequence[int],
    min_level: int,
    max_level: int,
) -> bool:
    """
    Проверяет, попадают ли все промежуточные значения в нужный диапазон сложности.
    """

    levels = [number_digit_level(value) for value in intermediate_values]
    return min(levels) >= min_level and max(levels) <= max_level


def generate_problem(
    template: ProblemTemplate,
    task_number: int,
    min_level: int,
    max_level: int,
    rng: random.Random,
    max_attempts: int = 10_000,
) -> Dict[str, object]:
    """
    Генерирует одну задачу. Если задача не подходит по сложности,
    пробует новые значения параметров.
    """

    for _ in range(max_attempts):
        params = {
            name: range_value.sample(rng)
            for name, range_value in template.parameter_ranges.items()
        }
        payload = template.builder(params)
        intermediate_values = payload["intermediate_values"]

        if matches_difficulty(intermediate_values, min_level, max_level):
            return build_problem_metadata(
                template=template,
                task_number=task_number,
                payload=payload,
                params=params,
                requested_min_level=min_level,
                requested_max_level=max_level,
            )

    raise RuntimeError(
        f"Не удалось сгенерировать задачу для шаблона '{template.code}' "
        f"с уровнем сложности от '{digit_level_label(min_level)}' до '{digit_level_label(max_level)}'."
    )


def parse_args() -> argparse.Namespace:
    """Описывает аргументы командной строки."""

    parser = argparse.ArgumentParser(
        description="Генератор математических задач с несколькими шаблонами."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Сколько задач нужно сгенерировать.",
    )
    parser.add_argument(
        "--template",
        default="any",
        help="Код шаблона. По умолчанию задачи выбираются из всех шаблонов.",
    )
    parser.add_argument(
        "--min-level",
        type=parse_digit_level,
        default=1,
        help="Минимальная сложность промежуточных чисел: 1, 2, 3, 4 или русское название.",
    )
    parser.add_argument(
        "--max-level",
        type=parse_digit_level,
        default=4,
        help="Максимальная сложность промежуточных чисел: 1, 2, 3, 4 или русское название.",
    )
    parser.add_argument(
        "--output",
        default="generated_problems.json",
        help="Путь к JSON-файлу для сохранения результата.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Зерно генератора случайных чисел для воспроизводимости результата.",
    )
    parser.add_argument(
        "--set-range",
        action="append",
        default=[],
        metavar="ШАБЛОН.ПАРАМЕТР=MIN:MAX",
        help="Переопределение диапазона параметра в конкретном шаблоне.",
    )

    args = parser.parse_args()

    if args.count <= 0:
        parser.error("Параметр --count должен быть положительным")
    if args.min_level > args.max_level:
        parser.error("Минимальный уровень сложности не может быть больше максимального")

    return args


def main() -> None:
    """Точка входа программы."""

    args = parse_args()
    rng = random.Random(args.seed)

    templates = create_templates()
    overrides = [parse_range_override(item) for item in args.set_range]
    templates = apply_range_overrides(templates, overrides)

    if args.template == "any":
        template_pool = list(templates.values())
    else:
        if args.template not in templates:
            available = ", ".join(sorted(templates))
            raise SystemExit(
                f"Шаблон '{args.template}' не найден. Доступные шаблоны: {available}"
            )
        template_pool = [templates[args.template]]

    generated_problems: List[Dict[str, object]] = []

    for task_number in range(1, args.count + 1):
        template = rng.choice(template_pool)
        generated_problems.append(
            generate_problem(
                template=template,
                task_number=task_number,
                min_level=args.min_level,
                max_level=args.max_level,
                rng=rng,
            )
        )

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(
            generated_problems,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Создано: {format_counted_noun(args.count, ('задача', 'задачи', 'задач'))}.")
    print(f"JSON сохранен в файл: {output_path}")
    print()

    for problem in generated_problems:
        print(f"Код: {problem['problem_code']}")
        print(f"Категория: {problem['category']} / {problem['problem_type']}")
        print(f"Условие: {problem['problem']}")
        print(f"Ответ: {problem['answer']}")
        print(
            "Сложность промежуточных чисел: "
            f"{problem['difficulty']['actual_min_label']} - {problem['difficulty']['actual_max_label']}"
        )
        print()


if __name__ == "__main__":
    main()
