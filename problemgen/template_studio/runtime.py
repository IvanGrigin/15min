"""Детерминированная генерация экземпляра активного Studio-шаблона."""

from __future__ import annotations

import random
import re
from fractions import Fraction
from typing import Any

from problemgen.russian.agreement import pluralize_ru
from problemgen.russian.characters import Character, characters_by_universe
from problemgen.russian.inflection import RussianNoun
from problemgen.russian.motion import profile_for
from problemgen.russian.noun_dict import NOUNS
from problemgen.russian.template_engine import format_scalar, render_template as render_russian_template
from problemgen.russian.toponyms import Toponym, hours_between, toponyms_in_region
from problemgen.russian.traits import TraitScale, scale_for, scale_ids
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
    # Только для топонимов: «откуда» с парным предлогом — «из Читы», «с Камчатки».
    # Парность выводится из предлога места и в данных не дублируется.
    "from",
    # Только для персонажа: надпись единицы скорости его способа передвижения —
    # «км/ч», «узлов», «км/с». Берётся из профиля, а не из текста шаблона.
    "speed_phrase",
    # Двузначная запись числа на табло: «12:05», а не «12:5». Формат общий
    # для всех шаблонов про время, поэтому это слот, а не выражение автора.
    "clock",
    # Ступени шкалы признаков: единственное число согласуется по роду слова,
    # к которому шкала привязана, множественное — общее.
    "one", "two", "three", "one_pl", "two_pl", "three_pl",
    # Для любого объекта с парадигмой: предлог «с»/«со» вместе с творительным
    # падежом — «со Свеном», но «с Нюшей». Выбор аллморфа нельзя доверить автору
    # шаблона: он зависит от формы слова, а слово выбирается случайно.
    "with",
})
SLOT_OPERATIONS = frozenset({"count", "agree", "g", "move"})
SUPPORTED_PARAMETER_TYPES = frozenset({
    "integer", "positive_integer", "nonnegative_integer", "decimal", "fraction",
    "boolean", "string", "word", "letter", "name", "choice", "integer_list", "word_list",
    # Морфологические типы: значение — объект с парадигмой, а не строка.
    "character", "noun", "location", "toponym",
    # Настоящая разница часовых поясов между двумя городами: берётся
    # из данных, чтобы задача не утверждала географической неправды.
    "toponym_offset",
    # Скорость, привязанная к персонажу: диапазон берётся из его способа
    # передвижения, а не пишется в шаблоне. Иначе автор задаёт «3 км/ч»
    # и получает гоночную машину, которая ползёт.
    "speed",
    # Коэффициент пересчёта малой единицы в основную: 1000 м в км, 10 кабельтовых
    # в морской миле. Нужен формулам, чтобы не зашивать «50/3» под километры.
    "motion_scale",
    # Числовой признак уже выбранного существительного: сколько ног у существа.
    # Формула получает его из словаря, поэтому «в караване 76 ног» остаётся
    # верным и когда вместо пони выпадает корова.
    "noun_trait",
    # Шкала признаков: чем задача различает три группы. Возраст, цвет, размер,
    # настроение. Без неё «молодые» и «старые» пишутся в тексте шаблона,
    # и одна и та же очередь выпадает во всех вселенных.
    "trait_scale",
})
# Признаки существительного, которые разрешено читать в формулу. Список закрыт
# намеренно: он же служит перечнем того, что обязано быть заполнено в словаре.
NOUN_TRAITS = frozenset({"legs"})
MAX_SAMPLING_ATTEMPTS = 300
SUPPORTED_ANSWER_TYPES = frozenset({
    "integer", "number", "decimal", "fraction", "boolean", "text", "list",
    "word", "word_list", "integer_list", "ordered_list", "multi_part", "cryptarithm_solutions",
})
MAX_RANGE = 100_000


class TemplateRuntimeError(ValueError):
    """Данные шаблона нельзя безопасно сгенерировать или отрендерить."""


def generate_active_template(
    template: dict[str, Any],
    rng: random.Random,
    allowed_universes: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Сгенерировать экземпляр: сэмплирование → derived → constraints → ответ → текст.

    Если заданы ``constraints``, набор чисел пересэмплируется до тех пор, пока все
    предикаты не станут истинными. Это единственный способ выразить «сдача
    положительна», «время делится на 5», «путь кратен 500 метрам» декларативно.

    ``allowed_universes`` сужает пул вселенных, из которого шаблон выбирает
    общий мир задачи (сеттинг: возрастной рейтинг, предпочтение по вкусу).
    Шаблоны без вселенной (числа, уравнения) фильтр не замечают.
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
        try:
            # Пустой пул при неудачном жребии — это отсев, а не дефект шаблона:
            # если первым выпал крайний восточный город, второму взяться неоткуда,
            # и набор просто разыгрывается заново. В список ошибок такое не идёт,
            # иначе валидатор объявит исправный шаблон сломанным.
            values, selected_universe = sample_parameters_with_story(schema, rng, allowed_universes)
        except TemplateRuntimeError as error:
            if "не осталось подходящих" not in str(error):
                errors.append(str(error))
            constraint_rejections += 1
            last_error = str(error)
            continue
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
        story_context = validate_story_context(
            resolve_story_profile(template.get("story_profile"), schema), schema, values, selected_universe
        )
        return {
            "rendered_problem": rendered,
            "parameters": values,
            "answer": normalize_value(answer),
            "answer_text": render_answer(template.get("answer_rendering"), normalize_value(answer), values),
            "story_context": story_context,
            "sampling": {
                "attempts": attempt,
                "constraint_rejections": constraint_rejections,
                "errors": errors,
            },
        }
    raise TemplateRuntimeError(
        f"За {MAX_SAMPLING_ATTEMPTS} попыток не удалось подобрать параметры: "
        f"{last_error or 'причина неизвестна'}."
    )


def resolve_story_profile(profile: Any, schema: dict[str, Any]) -> dict[str, Any]:
    """Получить профиль из JSON или безопасно классифицировать старую запись.

    Классификация опирается только на типы и источники параметров. Поэтому она
    не меняет математику и не пытается угадать сюжет по видимому имени.
    """
    if isinstance(profile, dict):
        return profile
    rules = [rule for rule in schema.values() if isinstance(rule, dict)]
    uses_world = any(
        rule.get("from_universe_items") or rule.get("from_universe_valuables")
        or rule.get("from_universe_currency") or rule.get("from_universe_folk")
        or (rule.get("type") == "character" and rule.get("universe") != "Обычные имена")
        for rule in rules
    )
    if uses_world:
        return {"mode": "universe", "same_universe": True, "inferred": True}
    if any(rule.get("type") == "character" for rule in rules):
        return {"mode": "common", "inferred": True}
    if any(rule.get("type") == "noun" and rule.get("legs") is not None for rule in rules):
        return {"mode": "neutral", "inferred": True}
    return {"mode": "abstract", "inferred": True}


def validate_story_context(
    profile: Any, schema: dict[str, Any], values: dict[str, Any], selected_universe: str | None
) -> dict[str, Any]:
    """Построить и проверить скрытый контекст сюжета по уже выбранным данным.

    Проверка намеренно использует идентификаторы и реестры, а не видимые имена:
    совпадающие имена из разных миров не могут обойти изоляцию вселенной.
    """
    mode = str(profile.get("mode", "abstract"))
    if mode not in {"universe", "common", "neutral", "abstract"}:
        raise TemplateRuntimeError(f"Неизвестный story_profile.mode: {mode!r}.")
    characters = [value for value in values.values() if isinstance(value, Character)]
    locations = [value for value in values.values() if isinstance(value, Location)]
    character_ids = [character.character_id for character in characters]
    if len(character_ids) != len(set(character_ids)):
        raise TemplateRuntimeError("В сюжетной задаче повторён character_id.")
    universes = {character.universe for character in characters if character.universe != "Обычные имена"}
    if mode == "universe":
        if profile.get("same_universe") is not True or selected_universe is None:
            raise TemplateRuntimeError("Universe-сюжет требует ровно одну вселенную персонажей.")
        universe = selected_universe
        if universes and universes != {universe}:
            raise TemplateRuntimeError("Персонаж принадлежит другой вселенной.")
        if any(location.universe != universe for location in locations):
            raise TemplateRuntimeError("Локация принадлежит другой вселенной.")
        registry = load_universes()
        if universe not in registry:
            raise TemplateRuntimeError("Для выбранной вселенной нет записи сущностей.")
        for name, rule in schema.items():
            if not isinstance(rule, dict) or rule.get("type") != "noun":
                continue
            source = next((key for key in ("items", "valuables", "currency", "folk")
                           if rule.get(f"from_universe_{key}")), None)
            if source and isinstance(values.get(name), RussianNoun):
                allowed = set(getattr(registry[universe], source))
                if source == "items":
                    allowed |= set(rule.get("fallback_lemmas") or [])
                if values[name].lemma not in allowed:
                    raise TemplateRuntimeError(
                        f"{name}: лемма не принадлежит {source} выбранной вселенной."
                    )
        return {
            "mode": mode,
            "universe": universe,
            "character_ids": character_ids,
            "location_ids": [location.location_id for location in locations],
            "checks": ["single_universe_valid"],
        }
    if mode == "common" and any(character.universe != "Обычные имена" for character in characters):
        raise TemplateRuntimeError("Common-сюжет не может использовать персонажей вселенных.")
    if mode in {"neutral", "abstract"} and characters:
        raise TemplateRuntimeError(f"Режим {mode} не допускает именованных персонажей.")
    return {"mode": mode, "universe": None, "character_ids": character_ids,
            "location_ids": [], "checks": [f"{mode}_valid"]}


def normalize_constraints(raw: Any) -> list[str]:
    """Привести constraints к списку строк-предикатов, приняв исторические форматы."""
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
    """Проверить, что набор значений удовлетворяет всем предикатам."""
    for predicate in constraints:
        result = evaluate_expression(predicate, values)
        if not isinstance(result, bool):
            raise TemplateRuntimeError(f"Constraint должен возвращать True/False: {predicate!r}.")
        if not result:
            return False
    return True


def sample_parameters(
    schema: dict[str, Any], rng: random.Random,
    allowed_universes: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Разыграть параметры без служебного контекста для совместимости API."""
    return sample_parameters_with_story(schema, rng, allowed_universes)[0]


def sample_parameters_with_story(
    schema: dict[str, Any], rng: random.Random,
    allowed_universes: frozenset[str] | None = None,
) -> tuple[dict[str, Any], str | None]:
    """Разыграть значения параметров: числа, персонажей, слова и локации."""
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
    story_universe = _sample_story_universe(schema, rng, allowed_universes)
    used_character_ids: set[str] = set()
    # Персонажи разыгрываются первыми: от способа их передвижения зависят
    # скорости и единицы измерения, поэтому порядок объявления в JSON
    # не должен влиять на результат.
    # Порядок разыгрывания задан зависимостями, а не порядком записи в JSON:
    # скорость зависит от персонажа, разница поясов — от двух городов.
    # Сортировка устойчивая, поэтому внутри одного ранга сохраняется
    # объявленный порядок: это важно для different_from и east_of.
    rank = {"character": 0, "toponym": 1}
    late = {"speed", "motion_scale", "toponym_offset", "noun_trait", "trait_scale"}
    ordered = sorted(
        schema.items(),
        key=lambda item: 3 if item[1]["type"] in late else rank.get(item[1]["type"], 2),
    )
    for name, rule in ordered:
        kind = rule["type"]
        if kind == "character":
            peers = sum(
                1 for other in schema.values()
                if isinstance(other, dict) and other.get("same_motion_as") == name
            )
            character = _sample_character(
                name, rule, rng, story_universe, used_character_ids, values, peers)
            used_character_ids.add(character.character_id)
            values[name] = character
        elif kind == "noun":
            values[name] = _sample_noun(name, rule, rng, story_universe, values)
        elif kind == "location":
            values[name] = _sample_location(name, rule, rng, story_universe)
        elif kind == "speed":
            values[name] = _sample_speed(name, rule, rng, values)
        elif kind == "toponym":
            values[name] = _sample_toponym(name, rule, rng, values)
        elif kind == "toponym_offset":
            values[name] = _sample_toponym_offset(name, rule, values)
        elif kind == "motion_scale":
            values[name] = profile_for(_motion_owner(name, rule, values).motion).small_per_main
        elif kind == "noun_trait":
            values[name] = _sample_noun_trait(name, rule, values)
        elif kind == "trait_scale":
            values[name] = _sample_trait_scale(name, rule, rng, values)
        else:
            values[name] = _sample_value(name, rule, rng)
    return values, story_universe


def _sample_trait_scale(
    name: str, rule: dict[str, Any], rng: random.Random, values: dict[str, Any]
) -> TraitScale:
    """Шкала признаков, согласованная с определяемым словом.

    ``agrees_with`` называет параметр-существительное, к которому относится
    определение: «красный житель», но «красная фея». Без согласования шкала
    ломает текст ровно там, где мир подставил слово другого рода.
    """
    owner = rule.get("agrees_with")
    if not isinstance(owner, str) or not isinstance(values.get(owner), RussianNoun):
        raise TemplateRuntimeError(
            f"Параметр {name}: 'agrees_with' должен ссылаться на параметр типа noun, "
            f"получено {owner!r}."
        )
    allowed = rule.get("scales")
    pool = list(allowed) if isinstance(allowed, list) and allowed else list(scale_ids())
    unknown = [item for item in pool if item not in scale_ids()]
    if unknown:
        raise TemplateRuntimeError(
            f"Параметр {name}: неизвестные шкалы признаков: {', '.join(unknown)}."
        )
    return scale_for(rng.choice(sorted(pool)), values[owner].gender)


def _sample_noun_trait(name: str, rule: dict[str, Any], values: dict[str, Any]) -> int:
    """Числовой признак выбранного существительного — например, число ног.

    Признак живёт в словаре рядом со словом, а не в шаблоне: иначе задача
    «в караване 76 ног и 26 голов» ломается ровно в тот момент, когда вместо
    пони выпадает гусь.
    """
    owner = rule.get("of")
    if not isinstance(owner, str) or not isinstance(values.get(owner), RussianNoun):
        raise TemplateRuntimeError(
            f"Параметр {name}: поле 'of' должно ссылаться на параметр типа noun, получено {owner!r}."
        )
    trait = str(rule.get("trait", ""))
    if trait not in NOUN_TRAITS:
        raise TemplateRuntimeError(
            f"Параметр {name}: признак {trait!r} читать нельзя. "
            f"Доступны: {', '.join(sorted(NOUN_TRAITS))}."
        )
    word = values[owner]
    value = getattr(word, trait)
    if value is None:
        raise TemplateRuntimeError(
            f"Параметр {name}: у слова {word.lemma!r} не заполнен признак {trait!r} "
            "в data/language/nouns/russian_nouns.json."
        )
    return int(value)


def _motion_owner(name: str, rule: dict[str, Any], values: dict[str, Any]) -> Character:
    """Персонаж, чей способ передвижения задаёт величину или единицу."""
    owner = rule.get("of") or rule.get("from_motion")
    if not isinstance(owner, str):
        raise TemplateRuntimeError(f"Параметр {name}: нужно поле 'of' с именем параметра-персонажа.")
    if owner not in values or not isinstance(values[owner], Character):
        raise TemplateRuntimeError(
            f"Параметр {name}: 'of' должен ссылаться на параметр типа character, получено {owner!r}."
        )
    return values[owner]


def _sample_toponym(
    name: str, rule: dict[str, Any], rng: random.Random, values: dict[str, Any]
) -> Toponym:
    """Город из реестра; можно ограничить группой и запретить повтор.

    ``different_from`` перечисляет параметры-топонимы, с которыми выбранный
    город не должен совпасть: маршрут «из Читы в Читу» смысла не имеет.
    """
    pool = list(toponyms_in_region(rule.get("region"), rule.get("kind")))
    preposition = rule.get("preposition")
    if isinstance(preposition, str):
        pool = [item for item in pool if item.preposition == preposition]
    east_of = rule.get("east_of")
    if isinstance(east_of, str):
        anchor = values.get(east_of)
        if not isinstance(anchor, Toponym):
            raise TemplateRuntimeError(f"Параметр {name}: east_of должен ссылаться на топоним.")
        low = int(rule.get("min_offset", 1))
        high = int(rule.get("max_offset", 12))
        pool = [item for item in pool if low <= hours_between(anchor, item) <= high]
    others = rule.get("different_from")
    if isinstance(others, str):
        others = [others]
    for other in others or []:
        chosen = values.get(other)
        if isinstance(chosen, Toponym):
            pool = [item for item in pool if item.toponym_id != chosen.toponym_id]
    if not pool:
        raise TemplateRuntimeError(f"Параметр {name}: не осталось подходящих городов.")
    return rng.choice(sorted(pool, key=lambda item: item.toponym_id))


def _sample_toponym_offset(name: str, rule: dict[str, Any], values: dict[str, Any]) -> int:
    """Разница часовых поясов между двумя выбранными городами, в часах."""
    west, east = rule.get("from"), rule.get("to")
    for role, key in (("from", west), ("to", east)):
        if not isinstance(key, str) or not isinstance(values.get(key), Toponym):
            raise TemplateRuntimeError(
                f"Параметр {name}: поле {role!r} должно ссылаться на параметр типа toponym."
            )
    return hours_between(values[west], values[east])


def _sample_speed(name: str, rule: dict[str, Any], rng: random.Random, values: dict[str, Any]) -> int:
    """Скорость в единицах способа передвижения персонажа.

    Диапазон берётся из профиля: пешеход получит 3–7 км/ч, гоночная машина
    40–160 км/ч, звездолёт 8–40 км/с. Шаблон может сузить диапазон долями
    от профильного через 'low' и 'high' (0.0–1.0), но не может выйти за него.
    """
    profile = profile_for(_motion_owner(name, rule, values).motion)
    span = profile.speed_max - profile.speed_min
    low = profile.speed_min + int(span * float(rule.get("low", 0.0)))
    high = profile.speed_min + int(span * float(rule.get("high", 1.0)))
    if low > high:
        raise TemplateRuntimeError(f"Параметр {name}: пустой диапазон скорости {low}..{high}.")
    step = int(rule.get("step", 1))
    if step < 1:
        raise TemplateRuntimeError(f"Параметр {name}: шаг должен быть не меньше 1.")
    choices = list(range(low, high + 1, step))
    return rng.choice(choices)


def _story_bound(rule: dict[str, Any]) -> bool:
    """По умолчанию персонажи и предметы одного шаблона берутся из одной вселенной."""
    return bool(rule.get("universe_binds", "story") == "story")


def _sample_story_universe(
    schema: dict[str, Any], rng: random.Random,
    allowed_universes: frozenset[str] | None = None,
) -> str | None:
    """Общая вселенная задачи выбирается один раз, до персонажей, локаций и предметов.

    ``allowed_universes`` — сеттинг сайта (возрастной рейтинг, вкус), а не
    требование самого шаблона: пустое пересечение с готовыми кандидатами —
    такой же отсев, что и нехватка персонажей нужного способа передвижения,
    а не повод объявить шаблон сломанным.
    """
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
        and (rule.get("from_universe_items") or rule.get("from_universe_valuables")
             or rule.get("from_universe_currency") or rule.get("from_universe_folk"))
        and _story_bound(rule)
        for rule in schema.values()
    )
    if not needed and not needs_place and not needs_items:
        return None
    registry = characters_by_universe()
    described = load_universes()

    def motion_ok(universe: str) -> bool:
        """Хватает ли в мире персонажей нужного способа передвижения.

        Проверять обязательно здесь: если выбрать мир раньше фильтра, попадётся
        вселенная вроде «Звёздных войн», где все летают на звездолётах, а шаблон
        просит пешеходов, и подбор упрётся в пустой пул.
        """
        rules = [
            rule for rule in schema.values()
            if isinstance(rule, dict) and rule.get("type") == "character" and _story_bound(rule)
        ]
        allowed = [rule.get("motion") for rule in rules if rule.get("motion")]
        bound = any(rule.get("same_motion_as") for rule in rules)
        if not allowed and not bound:
            return True
        modes: set[str] = set()
        for item in allowed:
            modes |= {item} if isinstance(item, str) else set(item)
        people = registry.get(universe, ())
        if bound:
            # Все связанные персонажи двигаются одинаково: нужен один способ,
            # которым владеют хотя бы столько героев, сколько просит шаблон.
            counts: dict[str, int] = {}
            for person in people:
                if not modes or person.motion in modes:
                    counts[person.motion] = counts.get(person.motion, 0) + 1
            return bool(counts) and max(counts.values()) >= len(rules)
        return sum(1 for person in people if person.motion in modes) >= len(rules)

    candidates = sorted(
        universe for universe, items in registry.items()
        if len(items) >= needed
        and motion_ok(universe)
        # Вселенная годится, только если в ней есть всё, что просит шаблон: хватает
        # персонажей, а при необходимости — описанные локации и предметы.
        and (not needs_place or (universe in described and described[universe].locations))
        and (not needs_items or (universe in described
                                 and (described[universe].items or described[universe].valuables
                                      or described[universe].currency
                                      or described[universe].folk)))
    )
    if not candidates:
        raise TemplateRuntimeError(
            f"Нет вселенной, где есть {needed} персонажа(ей) с готовыми падежами"
            + (", описанная локация" if needs_place else "")
            + (", список предметов" if needs_items else "")
            + "."
        )
    if allowed_universes is not None:
        narrowed = [universe for universe in candidates if universe in allowed_universes]
        if not narrowed:
            # Формулировка обязана содержать «не осталось подходящих» дословно:
            # именно по этой подстроке верхний уровень отличает отсев по сеттингу
            # (просто пересэмплировать) от настоящего дефекта шаблона.
            raise TemplateRuntimeError(
                "Сеттинг: не осталось подходящих вселенных для выбранного "
                "возрастного рейтинга или аудитории."
            )
        candidates = narrowed
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
            raise TemplateRuntimeError(
                f"Параметр {name}: вселенной {universe!r} нет в data/entities/universes.json."
            )
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
    values: dict[str, Any] | None = None,
    peers: int = 0,
) -> Character:
    """Персонаж из общей вселенной, с учётом рода и способа передвижения.

    ``peers`` — сколько других параметров привязаны к этому через
    ``same_motion_as``. Способ, которым в мире владеет один герой, тогда
    не годится: спутника взять будет неоткуда.
    """
    values = values or {}
    registry = characters_by_universe()
    universe = rule.get("universe") or (story_universe if _story_bound(rule) else None)
    if universe is not None and universe not in registry:
        raise TemplateRuntimeError(f"Параметр {name}: вселенной {universe!r} нет в реестре персонажей.")
    pool = list(registry[universe]) if universe else [item for items in registry.values() for item in items]
    allowed_motion = rule.get("motion")
    if isinstance(allowed_motion, str):
        allowed_motion = [allowed_motion]
    if isinstance(allowed_motion, list):
        # Шаблон вправе потребовать совместимый способ передвижения: сюжет
        # «догнал и подвёз» не работает, если один ползёт, а другой летит.
        pool = [character for character in pool if character.motion in allowed_motion]
    twin = rule.get("same_motion_as")
    if isinstance(twin, str):
        if twin not in values or not isinstance(values[twin], Character):
            raise TemplateRuntimeError(
                f"Параметр {name}: same_motion_as должен ссылаться на параметр-персонаж."
            )
        pool = [character for character in pool if character.motion == values[twin].motion]
    if peers:
        counts: dict[str, int] = {}
        for person in pool:
            counts[person.motion] = counts.get(person.motion, 0) + 1
        pool = [person for person in pool if counts[person.motion] > peers]
    age_twin = rule.get("same_age_class_as")
    if isinstance(age_twin, str):
        # Сравнивать по возрасту можно только ровесников: «мама Свинка старше
        # бабушки Свинки на 14 лет» проходит любую арифметическую проверку
        # и при этом неправда.
        if age_twin not in values or not isinstance(values[age_twin], Character):
            raise TemplateRuntimeError(
                f"Параметр {name}: same_age_class_as должен ссылаться на параметр-персонаж."
            )
        pool = [c for c in pool if c.age_class == values[age_twin].age_class]
    gender = rule.get("gender")
    if gender is not None:
        pool = [character for character in pool if character.gender == gender]
    pool = [character for character in pool if character.character_id not in used_character_ids]
    if not pool:
        raise TemplateRuntimeError(f"Параметр {name}: не осталось подходящих персонажей.")
    return rng.choice(sorted(pool, key=lambda character: character.character_id))


def _sample_noun(
    name: str, rule: dict[str, Any], rng: random.Random, story_universe: str | None,
    values: dict[str, Any] | None = None,
) -> RussianNoun:
    """Существительное: фиксированное, из списка, из предметов мира или из профиля движения."""
    if rule.get("from_universe_currency"):
        # Деньги мира: «поровну дублонов», а не «поровну гитар».
        registry = load_universes()
        if story_universe is None or story_universe not in registry:
            raise TemplateRuntimeError(
                f"Параметр {name}: from_universe_currency требует вселенной из universes.json."
            )
        pool = list(registry[story_universe].currency)
        if not pool:
            raise TemplateRuntimeError(f"Параметр {name}: у мира {story_universe!r} нет валюты.")
        return NOUNS[rng.choice(sorted(pool))]
    if rule.get("from_universe_folk"):
        # Обитатели мира: в очереди за похлёбкой стоят пираты, а в Хогвартсе —
        # волшебники. Слово берётся у вселенной, а не пишется в шаблоне.
        registry = load_universes()
        if story_universe is None or story_universe not in registry:
            raise TemplateRuntimeError(
                f"Параметр {name}: from_universe_folk требует вселенной из universes.json."
            )
        pool = list(registry[story_universe].folk)
        if not pool:
            raise TemplateRuntimeError(f"Параметр {name}: у мира {story_universe!r} нет обитателей.")
        return NOUNS[rng.choice(sorted(pool))]
    if rule.get("from_universe_valuables"):
        # Ценности мира: пираты делят дублоны, а не шоколадки. Список лежит
        # у вселенной, поэтому шаблон не перечисляет его у себя.
        registry = load_universes()
        if story_universe is None or story_universe not in registry:
            raise TemplateRuntimeError(
                f"Параметр {name}: from_universe_valuables требует вселенной из universes.json."
            )
        pool = list(registry[story_universe].valuables)
        if not pool:
            raise TemplateRuntimeError(f"Параметр {name}: у мира {story_universe!r} нет ценностей.")
        return NOUNS[rng.choice(sorted(pool))]
    if rule.get("from_motion"):
        # Единица расстояния зависит от способа передвижения: у корабля это
        # морская миля, у улитки сантиметр. Шаблон просит «основную» или «малую».
        profile = profile_for(_motion_owner(name, rule, values or {}).motion)
        scale = str(rule.get("scale", "main"))
        lemma = profile.small_distance_unit if scale == "small" else profile.distance_unit
        if lemma not in NOUNS:
            raise TemplateRuntimeError(
                f"Параметр {name}: единицы {lemma!r} из профиля нет в словаре существительных."
            )
        return NOUNS[lemma]
    lemma = rule.get("lemma")
    if isinstance(lemma, str):
        if lemma not in NOUNS:
            raise TemplateRuntimeError(
                f"Параметр {name}: слова {lemma!r} нет в data/language/nouns/russian_nouns.json."
            )
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
            raise TemplateRuntimeError(
                f"Параметр {name}: у вселенной {story_universe!r} пустой список предметов."
            )
        # Глагол задаёт класс предмета сильнее, чем мир: «съели» требует еды,
        # и без фильтра выходит «съели 108 факелов». Если в мире подходящего
        # предмета нет — берётся запасной список шаблона: у роботов еды не бывает.
        if rule.get("tags"):
            fitting = [lemma for lemma in pool
                       if set(rule["tags"]) & set(NOUNS[lemma].tags)]
            if not fitting:
                fallback = rule.get("fallback_lemmas")
                if not isinstance(fallback, list) or not fallback:
                    raise TemplateRuntimeError(
                        f"Параметр {name}: у мира {story_universe!r} нет предмета "
                        f"с тегами {rule['tags']}, а 'fallback_lemmas' не задан."
                    )
                missing = [item for item in fallback if item not in NOUNS]
                if missing:
                    raise TemplateRuntimeError(
                        f"Параметр {name}: нет в словаре: {', '.join(missing)}."
                    )
                fitting = list(fallback)
            pool = fitting
        return NOUNS[rng.choice(sorted(pool))]
    by_universe = rule.get("lemmas_by_universe")
    if isinstance(by_universe, dict) and by_universe:
        # Предметы «своей» вселенной: в Простоквашино не появится световой меч.
        pool = by_universe.get(story_universe) or by_universe.get("_default")
        if not isinstance(pool, list) or not pool:
            raise TemplateRuntimeError(
                f"Параметр {name}: для вселенной {story_universe!r} "
                "не задан список предметов и нет '_default'."
            )
        missing = [item for item in pool if item not in NOUNS]
        if missing:
            raise TemplateRuntimeError(
                f"Параметр {name}: нет в словаре существительных: {', '.join(missing)}."
            )
        return NOUNS[rng.choice(sorted(pool))]
    lemmas = rule.get("lemmas")
    if isinstance(lemmas, list) and lemmas:
        missing = [item for item in lemmas if item not in NOUNS]
        if missing:
            raise TemplateRuntimeError(
                f"Параметр {name}: нет в словаре существительных: {', '.join(missing)}."
            )
        return NOUNS[rng.choice(sorted(_filter_nouns(name, lemmas, rule, values or {})))]
    if rule.get("tags") or rule.get("legs") is not None:
        # Подбор по признакам: «любое двуногое существо». Перечислять слова
        # в шаблоне не нужно — новое животное в словаре попадёт в задачу само.
        return NOUNS[rng.choice(sorted(_filter_nouns(name, list(NOUNS), rule, values or {})))]
    raise TemplateRuntimeError(
        f"Параметр {name} типа noun требует lemma, список lemmas или отбор по признакам."
    )


def _filter_nouns(
    name: str, pool: list[str], rule: dict[str, Any], values: dict[str, Any]
) -> list[str]:
    """Отсеять из пула слова, не подходящие по тегам, числу ног и уже занятые.

    ``different_from`` перечисляет параметры-существительные, повторять которые
    нельзя: «на ферме куры и куры» — не задача.
    """
    tags = rule.get("tags")
    if isinstance(tags, str):
        tags = [tags]
    if isinstance(tags, list):
        wanted = set(tags)
        pool = [lemma for lemma in pool if wanted & set(NOUNS[lemma].tags)]
    legs = rule.get("legs")
    if legs is not None:
        allowed = {int(legs)} if isinstance(legs, int) else {int(item) for item in legs}
        pool = [lemma for lemma in pool if NOUNS[lemma].legs in allowed]
    others = rule.get("different_from")
    if isinstance(others, str):
        others = [others]
    for other in others or []:
        chosen = values.get(other)
        if isinstance(chosen, RussianNoun):
            pool = [lemma for lemma in pool if lemma != chosen.lemma]
    if not pool:
        raise TemplateRuntimeError(f"Параметр {name}: не осталось подходящих существительных.")
    return pool


def derive_values(expressions: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """Вычислить производные величины в порядке их зависимостей."""
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
            raise TemplateRuntimeError(
                f"Неразрешённая или циклическая зависимость derived-параметров: {names}."
            )
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
                    f"Неизвестная операция {operation!r} в слоте {{{fragment}}}. "
                    f"Доступны: {', '.join(sorted(SLOT_OPERATIONS))}."
                )
            if operation == "g":
                variants = [variant.strip() for variant in argument.split("|")]
                if len(variants) not in (2, 3) or any(not variant for variant in variants):
                    raise TemplateRuntimeError(
                        f"Слот {{{fragment}}}: нужны две или три формы через '|', "
                        "например {hero:g,купил|купила}."
                    )
            elif not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", argument):
                raise TemplateRuntimeError(
                    f"Слот {{{fragment}}}: после запятой ожидается имя числового параметра."
                )
        elif spec not in CASE_SPECS:
            raise TemplateRuntimeError(
                f"Неизвестный падеж {spec!r} в слоте {{{fragment}}}. "
                f"Доступны: {', '.join(sorted(CASE_SPECS))}."
            )


def render_template(template_text: str, values: dict[str, Any]) -> str:
    """Собрать текст задачи, подставив значения в слоты с учётом морфологии."""
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

    Если ответ — момент на часах, а не количество, у части указывается
    ``"format": "time_of_day"``: значение считается числом минут от полуночи
    и печатается как ``18:15``.

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
        if part.get("format") == "time_of_day":
            chunks.append(_format_time_of_day(part, normalize_value(values[key])))
            continue
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


def _format_time_of_day(part: dict[str, Any], value: Any) -> str:
    """Показать число минут от полуночи как время суток: 1095 -> «18:15».

    Нужен там, где ответ задачи — момент на часах, а не количество чего-либо.
    Без этого пришлось бы печатать «18 часов; 15 минут», что для времени
    читается неверно, либо отказываться от целого семейства задач.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TemplateRuntimeError(
            f"format=time_of_day требует целого числа минут от полуночи, получено {value!r}."
        )
    if not 0 <= value < 1440:
        raise TemplateRuntimeError(
            f"format=time_of_day: минуты от полуночи должны быть от 0 до 1439, получено {value}."
        )
    text = f"{value // 60:02d}:{value % 60:02d}"
    label = part.get("label")
    return f"{label} {text}" if isinstance(label, str) and label else text


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
    """Проверить, что посчитанный ответ соответствует объявленному типу."""
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
        return isinstance(answer, (list, tuple)) and all(
            isinstance(item, int) and not isinstance(item, bool) for item in answer
        )
    if answer_type in {"ordered_list", "multi_part", "cryptarithm_solutions"}:
        return isinstance(answer, (list, tuple))
    return False


def display_value(value: Any) -> str:
    """Представить число для показа человеку: дробное — через запятую."""
    if isinstance(value, list):
        return ", ".join(display_value(item) for item in value)
    return format_scalar(value)


def normalize_value(value: Any) -> Any:
    """Привести значение к JSON-совместимому виду на границе API."""
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
        if kind == "integer_list" and (
            not isinstance(picked, list) or any(not isinstance(item, int) for item in picked)
        ):
            raise TemplateRuntimeError(f"Параметр {name} типа integer_list требует списки целых чисел.")
        if kind == "word_list" and (
            not isinstance(picked, list) or any(not isinstance(item, str) for item in picked)
        ):
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
    if (isinstance(minimum, bool) or isinstance(maximum, bool)
            or not isinstance(minimum, (int, float))
            or not isinstance(maximum, (int, float))):
        raise TemplateRuntimeError(f"Параметр {name} требует числовые minimum и maximum.")
    if minimum > maximum or maximum - minimum > MAX_RANGE:
        raise TemplateRuntimeError(f"Диапазон параметра {name} некорректен или слишком велик.")
    return float(minimum), float(maximum)
