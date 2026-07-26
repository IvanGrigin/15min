"""Детерминированная генерация экземпляра активного Studio-шаблона."""

from __future__ import annotations

import random
import re
from fractions import Fraction
from typing import Any

from problemgen.russian.agreement import pluralize_ru
from problemgen.russian.characters import Character, characters_by_universe
from problemgen.russian.inflection import RussianNoun
from problemgen.russian.noun_dict import NOUNS
from problemgen.russian.template_engine import format_scalar, render_template as render_russian_template
from problemgen.russian.universes import Location, load_universes

from .safe_expressions import SafeExpressionError, evaluate_expression


# Слот: {key} | {key:case} | {key:op,arg}. Аргумент op может содержать варианты
# через "|" ({hero:g,купил|купила}), поэтому в нём разрешены буквы и пробелы.
SLOT_RE = re.compile(r"\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^{}]+?)\s*)?\}")
# Обратная совместимость: старое имя использовалось как «имя ключа в фигурных скобках».
PLACEHOLDER_RE = SLOT_RE
CASE_SPECS = frozenset({
    "nom", "gen", "dat", "acc", "ins", "pre",
    "nom_pl", "gen_pl", "dat_pl", "acc_pl", "ins_pl", "pre_pl",
    # Только для локаций: предлог вместе с падежом. «loc» — где («в Хогвартсе»,
    # «на пляже»), «dir» — куда («в Хогвартс», «на пляж»). Предлог нельзя вывести
    # из формы слова, поэтому он лежит в данных вместе с локацией.
    "loc", "dir",
    # Для любого объекта с парадигмой: предлог «с»/«со» вместе с творительным
    # падежом — «со Свеном», но «с Нюшей». Выбор аллморфа нельзя доверить автору
    # шаблона: он зависит от формы слова, а слово выбирается случайно.
    "with",
})
SLOT_OPERATIONS = frozenset({"count", "agree", "g"})
SUPPORTED_PARAMETER_TYPES = frozenset({
    "integer", "positive_integer", "nonnegative_integer", "decimal", "fraction",
    "boolean", "string", "word", "letter", "name", "choice", "integer_list", "word_list",
    # Морфологические типы: значение — объект с парадигмой, а не строка.
    "character", "noun", "location",
})
MAX_SAMPLING_ATTEMPTS = 300
SUPPORTED_ANSWER_TYPES = frozenset({
    "integer", "number", "decimal", "fraction", "boolean", "text", "list",
    "word", "word_list", "integer_list", "ordered_list", "multi_part", "cryptarithm_solutions",
})
MAX_RANGE = 100_000


class TemplateRuntimeError(ValueError):
    """Данные шаблона нельзя безопасно сгенерировать или отрендерить."""


def generate_active_template(template: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """Сгенерировать экземпляр: сэмплирование → derived → constraints → ответ → текст.

    Если заданы ``constraints``, набор чисел пересэмплируется до тех пор, пока все
    предикаты не станут истинными. Это единственный способ выразить «сдача
    положительна», «время делится на 5», «путь кратен 500 метрам» декларативно.
    """
    schema = template.get("parameter_schema", {})
    derived_expressions = template.get("derived_values", {})
    constraints = normalize_constraints(template.get("constraints"))
    answer_expression = str(template.get("answer_expression", ""))
    text = str(template.get("candidate_template_text", ""))
    last_error: str | None = None

    constraint_rejections = 0
    errors: list[str] = []

    for attempt in range(1, MAX_SAMPLING_ATTEMPTS + 1):
        values = sample_parameters(schema, rng)
        try:
            values.update(derive_values(derived_expressions, values))
            if not constraints_satisfied(constraints, values):
                constraint_rejections += 1
                last_error = "ни один набор параметров не удовлетворил constraints"
                continue
            answer = evaluate_expression(answer_expression, values)
        except (SafeExpressionError, TemplateRuntimeError, ValueError, ZeroDivisionError) as error:
            # Ошибка вычисления — это дефект шаблона, а не сознательный отсев:
            # её видно в отчёте валидации, даже если следующая попытка удалась.
            errors.append(str(error))
            last_error = str(error)
            continue
        rendered = render_template(text, values)
        return {
            "rendered_problem": rendered,
            "parameters": values,
            "answer": normalize_value(answer),
            "answer_text": render_answer(template.get("answer_rendering"), normalize_value(answer), values),
            "sampling": {
                "attempts": attempt,
                "constraint_rejections": constraint_rejections,
                "errors": errors,
            },
        }
    raise TemplateRuntimeError(
        f"За {MAX_SAMPLING_ATTEMPTS} попыток не удалось подобрать параметры: {last_error or 'причина неизвестна'}."
    )


def normalize_constraints(raw: Any) -> list[str]:
    if raw in (None, "", [], {}):
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        if not all(isinstance(item, str) and item.strip() for item in raw):
            raise TemplateRuntimeError("Constraints должны быть списком непустых строк-предикатов.")
        return list(raw)
    if isinstance(raw, dict):
        # Исторический формат анализатора: {"имя": "предикат"}.
        predicates = [value for value in raw.values() if isinstance(value, str) and value.strip()]
        return predicates
    raise TemplateRuntimeError("Constraints должны быть списком строк или объектом со строками.")


def constraints_satisfied(constraints: list[str], values: dict[str, Any]) -> bool:
    for predicate in constraints:
        result = evaluate_expression(predicate, values)
        if not isinstance(result, bool):
            raise TemplateRuntimeError(f"Constraint должен возвращать True/False: {predicate!r}.")
        if not result:
            return False
    return True


def sample_parameters(schema: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    if not isinstance(schema, dict):
        raise TemplateRuntimeError("Схема параметров должна быть JSON-объектом.")
    for name, rule in schema.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise TemplateRuntimeError("Имена параметров должны быть ASCII-идентификаторами.")
        if not isinstance(rule, dict):
            raise TemplateRuntimeError(f"Описание параметра {name} должно быть объектом.")
        if rule.get("type") not in SUPPORTED_PARAMETER_TYPES:
            raise TemplateRuntimeError(f"Неподдерживаемый тип параметра {rule.get('type')!r}.")

    values: dict[str, Any] = {}
    story_universe = _sample_story_universe(schema, rng)
    used_character_ids: set[str] = set()
    for name, rule in schema.items():
        kind = rule["type"]
        if kind == "character":
            character = _sample_character(name, rule, rng, story_universe, used_character_ids)
            used_character_ids.add(character.character_id)
            values[name] = character
        elif kind == "noun":
            values[name] = _sample_noun(name, rule, rng, story_universe)
        elif kind == "location":
            values[name] = _sample_location(name, rule, rng, story_universe)
        else:
            values[name] = _sample_value(name, rule, rng)
    return values


def _story_bound(rule: dict[str, Any]) -> bool:
    """По умолчанию персонажи и предметы одного шаблона берутся из одной вселенной."""
    return bool(rule.get("universe_binds", "story") == "story")


def _sample_story_universe(schema: dict[str, Any], rng: random.Random) -> str | None:
    """Общая вселенная задачи выбирается один раз, до персонажей, локаций и предметов."""
    needed = sum(
        1 for rule in schema.values()
        if isinstance(rule, dict) and rule.get("type") == "character" and _story_bound(rule)
    )
    needs_place = any(
        isinstance(rule, dict) and rule.get("type") == "location" and _story_bound(rule)
        for rule in schema.values()
    )
    needs_items = any(
        isinstance(rule, dict) and rule.get("type") == "noun"
        and rule.get("from_universe_items") and _story_bound(rule)
        for rule in schema.values()
    )
    if not needed and not needs_place and not needs_items:
        return None
    registry = characters_by_universe()
    described = load_universes()
    candidates = sorted(
        universe for universe, items in registry.items()
        if len(items) >= needed
        # Вселенная годится, только если в ней есть всё, что просит шаблон: хватает
        # персонажей, а при необходимости — описанные локации и предметы.
        and (not needs_place or (universe in described and described[universe].locations))
        and (not needs_items or (universe in described and described[universe].items))
    )
    if not candidates:
        raise TemplateRuntimeError(
            f"Нет вселенной, где есть {needed} персонажа(ей) с готовыми падежами"
            + (", описанная локация" if needs_place else "")
            + (", список предметов" if needs_items else "")
            + "."
        )
    return rng.choice(candidates)


def _sample_location(
    name: str,
    rule: dict[str, Any],
    rng: random.Random,
    story_universe: str | None,
) -> Location:
    universe = rule.get("universe") or (story_universe if _story_bound(rule) else None)
    registry = load_universes()
    if universe is not None:
        if universe not in registry:
            raise TemplateRuntimeError(f"Параметр {name}: вселенной {universe!r} нет в data/entities/universes.json.")
        pool = list(registry[universe].locations)
    else:
        pool = [location for entry in registry.values() for location in entry.locations]
    preposition = rule.get("preposition")
    if isinstance(preposition, str):
        pool = [location for location in pool if location.preposition == preposition]
    if not pool:
        raise TemplateRuntimeError(f"Параметр {name}: не осталось подходящих локаций.")
    return rng.choice(sorted(pool, key=lambda location: location.location_id))


def _sample_character(
    name: str,
    rule: dict[str, Any],
    rng: random.Random,
    story_universe: str | None,
    used_character_ids: set[str],
) -> Character:
    registry = characters_by_universe()
    universe = rule.get("universe") or (story_universe if _story_bound(rule) else None)
    if universe is not None and universe not in registry:
        raise TemplateRuntimeError(f"Параметр {name}: вселенной {universe!r} нет в реестре персонажей.")
    pool = list(registry[universe]) if universe else [item for items in registry.values() for item in items]
    gender = rule.get("gender")
    if gender is not None:
        pool = [character for character in pool if character.gender == gender]
    pool = [character for character in pool if character.character_id not in used_character_ids]
    if not pool:
        raise TemplateRuntimeError(f"Параметр {name}: не осталось подходящих персонажей.")
    return rng.choice(sorted(pool, key=lambda character: character.character_id))


def _sample_noun(name: str, rule: dict[str, Any], rng: random.Random, story_universe: str | None) -> RussianNoun:
    lemma = rule.get("lemma")
    if isinstance(lemma, str):
        if lemma not in NOUNS:
            raise TemplateRuntimeError(f"Параметр {name}: слова {lemma!r} нет в data/language/nouns/russian_nouns.json.")
        return NOUNS[lemma]
    if rule.get("from_universe_items"):
        # Предмет берётся из списка, описанного для вселенной в data/entities/universes.json,
        # чтобы не повторять один и тот же перечень в каждом шаблоне.
        registry = load_universes()
        if story_universe is None or story_universe not in registry:
            raise TemplateRuntimeError(
                f"Параметр {name}: from_universe_items требует вселенной, описанной в universes.json."
            )
        pool = list(registry[story_universe].items)
        if not pool:
            raise TemplateRuntimeError(f"Параметр {name}: у вселенной {story_universe!r} пустой список предметов.")
        return NOUNS[rng.choice(sorted(pool))]
    by_universe = rule.get("lemmas_by_universe")
    if isinstance(by_universe, dict) and by_universe:
        # Предметы «своей» вселенной: в Простоквашино не появится световой меч.
        pool = by_universe.get(story_universe) or by_universe.get("_default")
        if not isinstance(pool, list) or not pool:
            raise TemplateRuntimeError(
                f"Параметр {name}: для вселенной {story_universe!r} не задан список предметов и нет '_default'."
            )
        missing = [item for item in pool if item not in NOUNS]
        if missing:
            raise TemplateRuntimeError(f"Параметр {name}: нет в словаре существительных: {', '.join(missing)}.")
        return NOUNS[rng.choice(sorted(pool))]
    lemmas = rule.get("lemmas")
    if isinstance(lemmas, list) and lemmas:
        missing = [item for item in lemmas if item not in NOUNS]
        if missing:
            raise TemplateRuntimeError(f"Параметр {name}: нет в словаре существительных: {', '.join(missing)}.")
        return NOUNS[rng.choice(sorted(lemmas))]
    raise TemplateRuntimeError(
        f"Параметр {name} типа noun требует lemma или непустой список lemmas."
    )


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


def slot_keys(template_text: str) -> set[str]:
    """Имена параметров, на которые ссылается текст шаблона (включая аргументы count/agree)."""
    keys: set[str] = set()
    for key, spec in SLOT_RE.findall(template_text):
        keys.add(key)
        if spec and "," in spec:
            operation, argument = spec.split(",", 1)
            if operation.strip() in {"count", "agree"}:
                keys.add(argument.strip())
    return keys


def validate_slots(template_text: str) -> None:
    """Проверить синтаксис слотов до генерации: понятный текст ошибки автору шаблона."""
    for fragment in re.findall(r"\{([^{}]*)\}", template_text):
        match = SLOT_RE.fullmatch("{" + fragment + "}")
        if match is None:
            raise TemplateRuntimeError(f"Недопустимый слот {{{fragment}}}.")
        spec = (match.group(2) or "").strip()
        if not spec:
            continue
        if "," in spec:
            operation, argument = (part.strip() for part in spec.split(",", 1))
            if operation not in SLOT_OPERATIONS:
                raise TemplateRuntimeError(
                    f"Неизвестная операция {operation!r} в слоте {{{fragment}}}. Доступны: {', '.join(sorted(SLOT_OPERATIONS))}."
                )
            if operation == "g":
                variants = [variant.strip() for variant in argument.split("|")]
                if len(variants) not in (2, 3) or any(not variant for variant in variants):
                    raise TemplateRuntimeError(
                        f"Слот {{{fragment}}}: нужны две или три формы через '|', например {{hero:g,купил|купила}}."
                    )
            elif not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", argument):
                raise TemplateRuntimeError(f"Слот {{{fragment}}}: после запятой ожидается имя числового параметра.")
        elif spec not in CASE_SPECS:
            raise TemplateRuntimeError(
                f"Неизвестный падеж {spec!r} в слоте {{{fragment}}}. Доступны: {', '.join(sorted(CASE_SPECS))}."
            )


def render_template(template_text: str, values: dict[str, Any]) -> str:
    if not isinstance(template_text, str) or not template_text.strip() or len(template_text) > 20_000:
        raise TemplateRuntimeError("Текст шаблона должен быть непустой строкой не длиннее 20000 символов.")
    validate_slots(template_text)
    missing = sorted(slot_keys(template_text) - set(values))
    if missing:
        raise TemplateRuntimeError(f"Не определены плейсхолдеры: {', '.join(missing)}.")
    try:
        rendered = render_russian_template(template_text, values)
    except (KeyError, TypeError, ValueError) as error:
        raise TemplateRuntimeError(f"Ошибка рендеринга: {error}") from error
    if "{" in rendered or "}" in rendered:
        raise TemplateRuntimeError("После рендеринга остались неразрешённые плейсхолдеры.")
    return rendered


def render_answer(rendering: Any, answer: Any, values: dict[str, Any]) -> str | None:
    """Собрать текст ответа с согласованием единиц: «15,5 километра», «10 минут».

    Формат ``answer_rendering``::

        {"parts": [{"label": "а)", "value": "foot_km", "unit": "километр"},
                    {"label": "б)", "value": "ride_min", "unit": "минута"}]}

    ``value`` — имя параметра или derived-значения; ``unit`` — лемма из
    data/language/nouns/russian_nouns.json. Если единица измерения сама выбирается
    случайно (шаблон сравнивает «олимпиады» или «викторины» — см. type: noun
    с несколькими lemmas), вместо фиксированного ``unit`` укажите ``unit_param`` —
    имя параметра, чьё значение уже является существительным (RussianNoun),
    и ответ согласуется именно с тем словом, что попало в текст задачи.
    Если ни одно из полей не задано, возвращается None и работает прежнее
    поведение сайта.
    """
    if not isinstance(rendering, dict):
        return None
    parts = rendering.get("parts")
    if not isinstance(parts, list) or not parts:
        return None
    chunks: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            raise TemplateRuntimeError("Каждая часть answer_rendering должна быть объектом.")
        key = part.get("value")
        if not isinstance(key, str) or key not in values:
            raise TemplateRuntimeError(f"answer_rendering ссылается на неизвестное значение {key!r}.")
        unit_param = part.get("unit_param")
        if isinstance(unit_param, str):
            if unit_param not in values or not isinstance(values[unit_param], RussianNoun):
                raise TemplateRuntimeError(
                    f"answer_rendering: unit_param {unit_param!r} должен ссылаться на параметр типа noun."
                )
            text = _with_noun(normalize_value(values[key]), values[unit_param])
        else:
            text = _with_unit(normalize_value(values[key]), part.get("unit"))
        label = part.get("label")
        chunks.append(f"{label} {text}" if isinstance(label, str) and label else text)
    return "; ".join(chunks)


def _with_unit(value: Any, unit: Any) -> str:
    number = display_value(value)
    if not isinstance(unit, str) or not unit:
        return number
    if unit not in NOUNS:
        raise TemplateRuntimeError(f"Единицы {unit!r} нет в словаре существительных.")
    return _with_noun(value, NOUNS[unit])


def _with_noun(value: Any, noun: RussianNoun) -> str:
    number = display_value(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{number} {pluralize_ru(value, noun.count_forms())}"
    # Дробное количество управляет родительным падежом единственного числа:
    # «15,5 километра», «2,5 часа».
    return f"{number} {noun.gen}"


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
    if answer_type == "word":
        return isinstance(answer, str)
    if answer_type == "word_list":
        return isinstance(answer, (list, tuple)) and all(isinstance(item, str) for item in answer)
    if answer_type == "integer_list":
        return isinstance(answer, (list, tuple)) and all(isinstance(item, int) and not isinstance(item, bool) for item in answer)
    if answer_type in {"ordered_list", "multi_part", "cryptarithm_solutions"}:
        return isinstance(answer, (list, tuple))
    return False


def display_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(display_value(item) for item in value)
    return format_scalar(value)


def normalize_value(value: Any) -> Any:
    if hasattr(value, "get_case"):
        # Персонаж или существительное: наружу отдаём именительный падеж,
        # чтобы parameters оставались JSON-сериализуемыми.
        return getattr(value, "nom", str(value))
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
