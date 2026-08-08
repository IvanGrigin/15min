"""Прикладной сервис состояний, проверки и публикации Template Studio."""

from __future__ import annotations

import re
import uuid
from copy import deepcopy
from typing import Any

from .analyzer import TemplateAnalyzer
from .runtime import (
    normalize_constraints,
    SUPPORTED_ANSWER_TYPES,
    SUPPORTED_PARAMETER_TYPES,
    TemplateResampleError,
    TemplateRuntimeError,
    alphabet_derived_names,
    alphabet_owner_names,
    alphabet_referenced_names,
    answer_type_matches,
    digit_selection_names,
    digit_selection_sources,
    calendar_names,
    calendar_sources,
    reachability_names,
    reachability_sources,
    search_puzzle_names,
    star_addition_names,
    star_addition_sources,
    clock_search_names,
    clock_search_sources,
    factor_pair_names,
    max_digit_sum_names,
    restoration_names,
    factor_pair_sources,
    solver_sources,
    range_count_names,
    range_count_sources,
    story_variant_parameters,
    derive_values,
    generate_active_template,
    normalize_value,
    render_template,
    sample_parameters,
    slot_keys,
    validate_slots,
)
from .safe_expressions import SafeExpressionError, evaluate_expression, validate_expression
from .storage import TemplateStudioStore, utc_now


TEMPLATE_ID_RE = re.compile(r"[a-z][a-z0-9_]{2,80}\Z")
EDITABLE_FIELDS = frozenset({
    "template_id", "module_id", "candidate_template_text", "answer_type", "parameter_schema",
    "derived_values", "constraints", "solver_strategy", "answer_expression", "answer_rendering",
    "grammar_metadata", "source_metadata", "story_profile", "story_variants", "parameter_variants",
    "notes", "language", "abstract_story_exemption", "structure_signature", "principal_operation",
})
KNOWN_STRATEGIES = frozenset({"formula", "manual"})


class TemplateStudioService:
    """Сервис хранит все переходы статусов и не публикует непроверенные drafts."""

    def __init__(
        self,
        store: TemplateStudioStore | None = None,
        analyzer: TemplateAnalyzer | None = None,
    ) -> None:
        self.store = store or TemplateStudioStore()
        self.analyzer = analyzer or TemplateAnalyzer()

    def create_from_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Создать черновик из исходного текста задачи."""
        original_text = payload.get("original_text")
        if not isinstance(original_text, str) or not original_text.strip():
            raise ValueError("Original mathematical problem обязателен.")
        if len(original_text) > 20_000:
            raise ValueError("Исходный текст не должен превышать 20000 символов.")
        analysis = self.analyzer.analyze(original_text).values
        now = utc_now()
        draft_id = f"draft_{uuid.uuid4().hex}"
        template_id = str(payload.get("template_id") or f"studio_{uuid.uuid4().hex[:10]}").lower()
        draft = {
            "schema_version": 1,
            "draft_id": draft_id,
            "status": "draft",
            "created_at": now,
            "updated_at": now,
            "original_text": analysis["original_text"],
            "normalized_text": analysis["normalized_text"],
            "candidate_template_text": analysis["candidate_template_text"],
            "template_id": template_id,
            "module_id": self._optional_string(payload.get("module_id")),
            "language": str(payload.get("language") or "ru"),
            "answer_type": str(payload.get("answer_type") or analysis["detected_answer_type"]),
            "parameter_schema": analysis["candidate_parameters"],
            "derived_values": analysis["candidate_derived_values"],
            "constraints": analysis["candidate_constraints"],
            "solver_strategy": analysis["candidate_solver_strategy"],
            "answer_expression": analysis["candidate_answer_expression"],
            "answer_rendering": {"type": str(payload.get("answer_type") or analysis["detected_answer_type"])},
            "grammar_metadata": {},
            "story_profile": {"mode": "abstract"},
            "source_metadata": {
                "problem_number": self._optional_string(payload.get("source_problem_number")),
                "filename": self._optional_string(payload.get("source_filename")),
            },
            "notes": "",
            "analysis": analysis,
            "validation_report": None,
            "revision_history": [],
        }
        self._event(draft, "draft_created")
        self._event(draft, "analysis_run", details={
            "warnings": analysis["warnings"],
            "unsupported_features": analysis["unsupported_features"],
        })
        return self.store.save_draft(draft)

    def update_draft(self, draft_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        """Изменить разрешённые поля черновика."""
        draft = self.store.load_draft(draft_id)
        if draft["status"] not in {"draft", "validated"}:
            raise ValueError("Редактировать можно только черновик или validated-шаблон.")
        unknown = set(changes) - EDITABLE_FIELDS
        if unknown:
            raise ValueError(f"Нельзя редактировать системные поля: {', '.join(sorted(unknown))}.")
        for field, value in changes.items():
            text_fields = {
                "template_id", "candidate_template_text", "answer_type",
                "solver_strategy", "answer_expression", "language", "notes", "abstract_story_exemption",
                "structure_signature", "principal_operation",
            }
            if field in text_fields and not isinstance(value, str):
                raise ValueError(f"Поле {field} должно быть строкой.")
            object_fields = {
                "parameter_schema", "derived_values", "answer_rendering",
                "grammar_metadata", "source_metadata",
                "story_profile",
            }
            if field in object_fields and not isinstance(value, dict):
                raise ValueError(f"Поле {field} должно быть JSON-объектом.")
            if field in {"story_variants", "parameter_variants"} and not isinstance(value, list):
                raise ValueError(f"Поле {field} должно быть JSON-списком.")
            if field == "constraints" and not isinstance(value, (dict, list)):
                raise ValueError("Поле constraints должно быть списком предикатов или объектом.")
            if field == "module_id" and value is not None and not isinstance(value, str):
                raise ValueError("module_id должен быть строкой или null.")
            draft[field] = deepcopy(value)
        draft["status"] = "draft"
        draft["validation_report"] = None
        self._event(draft, "draft_edited", details={"fields": sorted(changes)})
        return self.store.save_draft(draft)

    def preview(self, draft_id: str, *, count: int = 3, seed: int = 1) -> dict[str, Any]:
        """Показать несколько детерминированных примеров по черновику."""
        if not isinstance(count, int) or not 1 <= count <= 20:
            raise ValueError("Количество предпросмотров должно быть целым числом от 1 до 20.")
        if not isinstance(seed, int):
            raise ValueError("Seed должен быть целым числом.")
        draft = self.store.load_draft(draft_id)
        previews: list[dict[str, Any]] = []
        import random
        for index in range(count):
            preview_seed = seed + index
            try:
                generated = generate_active_template(draft, random.Random(preview_seed))
                values = generated["parameters"]
                previews.append({
                    "seed": preview_seed,
                    "rendered_problem": generated["rendered_problem"],
                    "parameters": {name: normalize_value(values[name]) for name in draft["parameter_schema"]},
                    "derived_values": {
                        name: normalize_value(values[name]) for name in draft["derived_values"]
                    },
                    "answer": generated["answer"],
                    "validation": {"passed": True, "message": "Экземпляр сгенерирован."},
                })
            except (TemplateRuntimeError, SafeExpressionError, ValueError) as error:
                previews.append({
                    "seed": preview_seed, "rendered_problem": None,
                    "parameters": {}, "derived_values": {}, "answer": None,
                    "validation": {"passed": False, "message": str(error)},
                })
        self._event(draft, "preview_generated", details={"count": count, "seed": seed})
        self.store.save_draft(draft)
        return {"draft_id": draft_id, "previews": previews}

    def validate(
        self, draft_id: str, *, known_module_ids: set[str], existing_template_ids: set[str]
    ) -> dict[str, Any]:
        """Прогнать черновик через все проверки и сохранить отчёт."""
        draft = self.store.load_draft(draft_id)
        if draft["status"] not in {"draft", "validated", "archived"}:
            raise ValueError("Этот статус нельзя валидировать.")
        checks: list[dict[str, Any]] = []

        def check(identifier: str, label: str, action: Any) -> None:
            try:
                message = action()
                checks.append({"id": identifier, "label": label, "passed": True, "message": message or "OK"})
            except (ValueError, TypeError, SafeExpressionError, TemplateRuntimeError) as error:
                checks.append({"id": identifier, "label": label, "passed": False, "message": str(error)})

        check("schema", "Корректная структура черновика", lambda: self._check_schema(draft))
        check("template_id", "Уникальный template ID",
              lambda: self._check_template_id(draft, existing_template_ids))
        check("module", "Известный модуль", lambda: self._check_module(draft, known_module_ids))
        check("strategy", "Поддерживаемая стратегия", lambda: self._check_strategy(draft))
        check("placeholders", "Плейсхолдеры определены", lambda: self._check_placeholders(draft))
        check("parameters", "Ограниченная схема параметров", lambda: self._check_parameters(draft))
        check("expressions", "Безопасные derived- и answer-выражения", lambda: self._check_expressions(draft))
        check("student_text", "Текст для ученика не раскрывает ответ",
              lambda: self._check_student_text(draft))
        check("russian", "Базовая русская пунктуация и метаданные", lambda: self._check_russian(draft))
        check("story_profile", "Декларативный сюжетный профиль", lambda: self._check_story_profile(draft))
        check("variants", "Сюжетные и параметрические варианты", lambda: self._check_variants(draft))
        examples = self._validate_examples(draft, checks)
        passed = all(item["passed"] for item in checks)
        report = {
            "draft_id": draft_id, "validated_at": utc_now(), "passed": passed,
            "checks": checks, "successful_examples": examples,
        }
        draft["validation_report"] = report
        if passed:
            draft["status"] = "validated"
            self._event(draft, "validation_passed", details={"successful_examples": examples})
        else:
            draft["status"] = "draft"
            self._event(draft, "validation_failed", details={"successful_examples": examples})
        self.store.save_report(draft_id, report)
        self.store.save_draft(draft)
        return report

    def activate(
        self, draft_id: str, *, known_module_ids: set[str], existing_template_ids: set[str]
    ) -> dict[str, Any]:
        """Опубликовать проверенный черновик в активный каталог."""
        draft = self.store.load_draft(draft_id)
        if draft["status"] != "validated" or not draft.get("validation_report", {}).get("passed"):
            raise ValueError("Активировать можно только успешно validated-шаблон.")
        self._check_module(draft, known_module_ids)
        active_ids = {item.get("template_id", "") for item in self.store.load_active_templates()}
        self._check_template_id(draft, existing_template_ids | active_ids)
        active_template = self._active_payload(draft)
        self.store.activate(active_template)
        draft["status"] = "active"
        self._event(draft, "activated", details={
            "module_id": draft["module_id"], "template_id": draft["template_id"],
        })
        return self.store.save_draft(draft)

    def archive(self, draft_id: str) -> dict[str, Any]:
        """Убрать шаблон из активного каталога, сохранив историю."""
        draft = self.store.load_draft(draft_id)
        if draft["status"] != "active":
            raise ValueError("Архивировать можно только active-шаблон.")
        self.store.archive_active(draft["template_id"])
        draft["status"] = "archived"
        self._event(draft, "archived")
        return self.store.save_draft(draft)

    def restore(
        self, draft_id: str, *, known_module_ids: set[str], existing_template_ids: set[str]
    ) -> dict[str, Any]:
        """Вернуть архивный шаблон в активный каталог после проверки."""
        draft = self.store.load_draft(draft_id)
        if draft["status"] != "archived":
            raise ValueError("Восстановить можно только archived-шаблон.")
        report = self.validate(
            draft_id, known_module_ids=known_module_ids,
            existing_template_ids=existing_template_ids,
        )
        if not report["passed"]:
            raise ValueError("Восстановление остановлено: шаблон не прошёл текущую валидацию.")
        restored = self.activate(
            draft_id, known_module_ids=known_module_ids,
            existing_template_ids=existing_template_ids,
        )
        self._event(restored, "restored")
        return self.store.save_draft(restored)

    def reject(self, draft_id: str, reason: str) -> dict[str, Any]:
        """Отклонить черновик с указанием причины."""
        draft = self.store.load_draft(draft_id)
        if draft["status"] not in {"draft", "validated"}:
            raise ValueError("Отклонить можно только draft или validated-шаблон.")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
            raise ValueError("Укажите причину отклонения не длиннее 1000 символов.")
        draft["status"] = "rejected"
        self._event(draft, "rejected", details={"reason": reason.strip()})
        return self.store.save_draft(draft)

    def delete_draft(self, draft_id: str, *, confirmed: bool) -> None:
        """Удалить черновик навсегда; активный шаблон так удалить нельзя."""
        draft = self.store.load_draft(draft_id)
        if not confirmed:
            raise ValueError("Удаление черновика требует подтверждения.")
        if draft["status"] != "draft":
            raise ValueError("Навсегда удалить можно только draft; active-шаблоны архивируются.")
        event = {"at": utc_now(), "action": "deleted", "details": {}}
        self.store.append_history(draft_id, event)
        self.store.delete_draft_file(draft_id)

    def _validate_examples(self, draft: dict[str, Any], checks: list[dict[str, Any]]) -> int:
        import random
        successful = 0
        attempts = 0
        rejections = 0
        answer_type = draft.get("answer_type")
        for seed in range(10):
            try:
                generated = generate_active_template(draft, random.Random(seed))
                sampling = generated.get("sampling", {})
                attempts += int(sampling.get("attempts", 1))
                rejections += int(sampling.get("constraint_rejections", 0))
                if sampling.get("errors"):
                    # Ошибка вычисления при подборе чисел — дефект шаблона: без этой
                    # проверки rejection sampling молча прятал бы деление на ноль.
                    raise ValueError(f"ошибка при подборе параметров: {sampling['errors'][0]}")
                expression = generated.get("answer_expression") or draft["answer_expression"]
                independent = evaluate_expression(expression, generated["parameters"])
                normalized_independent = normalize_value(independent)
                if generated["answer"] != normalized_independent:
                    raise ValueError("Независимый расчёт не совпал с ответом шаблона.")
                expected_type = generated.get("answer_type") or answer_type
                if not answer_type_matches(normalized_independent, expected_type):
                    raise ValueError(f"Ответ не соответствует типу {expected_type}.")
                successful += 1
            except (ValueError, TemplateRuntimeError, SafeExpressionError) as error:
                checks.append({
                    "id": "examples",
                    "label": "Детерминированные примеры и независимый расчёт",
                    "passed": False, "message": f"seed {seed}: {error}",
                })
                return successful
        acceptance = f"{100 * successful / attempts:.0f}%" if attempts else "—"
        checks.append({
            "id": "examples",
            "label": "Детерминированные примеры и независимый расчёт",
            "passed": True,
            "message": (
                f"Проверено {successful} seed; попыток подбора {attempts}, "
                f"отсеяно constraints {rejections}, доля удачных {acceptance}."
            ),
        })
        return successful

    @staticmethod
    def _check_schema(draft: dict[str, Any]) -> str:
        required = {
            "draft_id", "status", "original_text", "candidate_template_text",
            "parameter_schema", "derived_values", "answer_expression",
        }
        missing = required - set(draft)
        if missing:
            raise ValueError(f"Нет обязательных полей: {', '.join(sorted(missing))}.")
        if not isinstance(draft["parameter_schema"], dict) or not isinstance(draft["derived_values"], dict):
            raise ValueError("Parameter schema и derived values должны быть объектами.")
        return "Структура draft JSON корректна."

    @staticmethod
    def _check_template_id(draft: dict[str, Any], existing_ids: set[str]) -> str:
        template_id = draft.get("template_id", "")
        if not isinstance(template_id, str) or not TEMPLATE_ID_RE.fullmatch(template_id):
            raise ValueError("template_id: строчные латинские буквы, цифры и _, длина 3–81, первая буква.")
        if template_id in existing_ids:
            raise ValueError(f"template_id {template_id} уже занят.")
        return "ID уникален среди активных каталогов."

    @staticmethod
    def _check_module(draft: dict[str, Any], known_module_ids: set[str]) -> str:
        module_id = draft.get("module_id")
        if not module_id:
            raise ValueError("Для активации выберите существующий target module.")
        if module_id not in known_module_ids:
            raise ValueError(f"Неизвестный module_id: {module_id}.")
        return "Модуль существует в каталоге сайта."

    @staticmethod
    def _check_strategy(draft: dict[str, Any]) -> str:
        strategy = draft.get("solver_strategy")
        if strategy not in KNOWN_STRATEGIES or strategy == "manual":
            raise ValueError("Для активации нужен поддерживаемый solver strategy formula.")
        return "Solver strategy зарегистрирована."

    @classmethod
    def _check_placeholders(cls, draft: dict[str, Any]) -> str:
        text = draft.get("candidate_template_text", "")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Текст шаблона пуст.")
        validate_slots(text)
        placeholders = slot_keys(text)
        schema = dict(draft.get("parameter_schema", {}))
        # Сюжетный вариант вправе завести собственный параметр — героя, место.
        # В каноническом тексте он не встречается, но объявленным считается.
        schema.update(story_variant_parameters(draft))
        bundle_outputs = cls._bundle_outputs(schema)
        defined = set(schema) | bundle_outputs | set(draft.get("derived_values", {}))
        defined |= (alphabet_derived_names(schema) | digit_selection_names(schema)
                    | range_count_names(schema) | factor_pair_names(schema)
                     | max_digit_sum_names(schema)
                     | restoration_names(schema)
                     | restoration_names(schema)
                    | clock_search_names(schema)
                    | calendar_names(schema)
                    | star_addition_names(schema)
                    | reachability_names(schema)
                    | search_puzzle_names(schema))
        missing = placeholders - defined
        if missing:
            raise ValueError(f"Не определены плейсхолдеры: {', '.join(sorted(missing))}.")
        used = placeholders | cls._expression_variables(draft) | alphabet_referenced_names(schema)
        # Идентификатор правила отбора в текст не попадает: в условии стоят
        # слова («однообразным»), а решателю нужен сам идентификатор.
        # Для проверки «неиспользуемых параметров» такая ссылка — использование.
        used |= (digit_selection_sources(schema) | range_count_sources(schema)
                 | factor_pair_sources(schema) | clock_search_sources(schema)
                 | calendar_sources(schema) | star_addition_names(schema)
                 | star_addition_sources(schema) | reachability_sources(schema)
                 | solver_sources(schema))
        # Решатели кладут производные значения рядом с собой; если в тексте
        # или в ответе стоит производное, использован и сам параметр.
        derived_by_type = {
            "digit_selection": ("_numbers", "_sum"),
            "clock_search": ("_h", "_m", "_s", "_gap", "_gap_m", "_gap_s"),
            "month_weekday_clue": ("_first", "_first_name", "_answer_day"),
            "star_addition": ("_first", "_second", "_total"),
            "elevator_reach": ("_reachable", "_possible"),
            "digit_deletion": ("_count",),
            "rectangle_cuts": ("_total",),
            "iterated_process": ("_peak",),
            "weight_set": ("_list", "_max"),
            "date_shift": ("_year", "_month", "_day", "_weekday", "_weekday_name",
                           "_yday", "_start_weekday", "_start_weekday_name"),
            "factor_pair": ("_useful",),
            "max_digit_sum": ("_number", "_count"),
            "swap_restore": ("_first", "_second", "_total", "_second_addend"),
            "replacement_restore": ("_first", "_second", "_total", "_second_addend"),
            "subsequence_count": ("_source",),
            "range_count": ("_pool",),
        }
        for name, rule in schema.items():
            if not isinstance(rule, dict):
                continue
            suffixes = derived_by_type.get(rule.get("type"))
            if suffixes and ({f"{name}{suffix}" for suffix in suffixes} & used):
                used.add(name)
        # Параметр, который встречается только в тексте сюжетного варианта,
        # используется — просто не в каноническом тексте.
        for story in draft.get("story_variants") or ():
            if isinstance(story, dict):
                variant_text = story.get("text", story.get("candidate_template_text"))
                if isinstance(variant_text, str):
                    used |= slot_keys(variant_text)
        unused = {
            name for name, rule in schema.items()
            if name not in used
            and not (
                isinstance(rule, dict) and rule.get("type") == "bundle"
                and bool(set(rule.get("bind", {}).values()) & used)
            )
        }
        if unused:
            raise ValueError(f"Неиспользуемые обязательные параметры: {', '.join(sorted(unused))}.")
        return "Все плейсхолдеры и обязательные параметры согласованы."

    @staticmethod
    def _check_parameters(draft: dict[str, Any]) -> str:
        schema = draft["parameter_schema"]
        if not schema:
            raise ValueError("Нужен хотя бы один independently generated параметр.")
        for name, rule in schema.items():
            if not isinstance(rule, dict) or rule.get("type") not in SUPPORTED_PARAMETER_TYPES:
                raise ValueError(f"Параметр {name} имеет неподдерживаемый type.")
        # Несколько попыток, потому что пустой пул при неудачном жребии — это
        # отсев, а не ошибка схемы: город восточнее крайнего восточного не найдётся.
        import random as _random

        last: Exception | None = None
        for seed in range(20):
            try:
                sample_parameters(schema, _random.Random(seed))
                return "Типы параметров и границы генерации корректны."
            except TemplateRuntimeError as error:
                rejected = isinstance(error, TemplateResampleError)
                if not rejected and "не осталось подходящих" not in str(error):
                    raise
                last = error
        raise ValueError(f"За 20 попыток не удалось разыграть параметры: {last}")

    @classmethod
    def _check_expressions(cls, draft: dict[str, Any]) -> str:
        schema = draft["parameter_schema"]
        variables = (set(schema) | cls._bundle_outputs(schema)
                     | alphabet_derived_names(schema) | digit_selection_names(schema)
                     | range_count_names(schema) | factor_pair_names(schema)
                     | max_digit_sum_names(schema)
                     | restoration_names(schema)
                     | restoration_names(schema)
                     | clock_search_names(schema) | calendar_names(schema)
                     | star_addition_names(schema) | reachability_names(schema)
                     | search_puzzle_names(schema))
        unresolved = dict(draft["derived_values"])
        while unresolved:
            progressed = False
            for name, expression in list(unresolved.items()):
                try:
                    validate_expression(str(expression), variables)
                except SafeExpressionError as error:
                    if "Неизвестная переменная" in str(error):
                        continue
                    raise ValueError(f"Derived {name}: {error}") from error
                variables.add(name)
                del unresolved[name]
                progressed = True
            if not progressed:
                raise ValueError("В derived expressions есть неизвестная переменная или цикл.")
        try:
            validate_expression(str(draft.get("answer_expression", "")), variables)
        except SafeExpressionError as error:
            raise ValueError(f"Answer expression: {error}") from error
        for predicate in normalize_constraints(draft.get("constraints")):
            try:
                validate_expression(predicate, variables)
            except SafeExpressionError as error:
                raise ValueError(f"Constraint {predicate!r}: {error}") from error
        if draft.get("answer_type") not in SUPPORTED_ANSWER_TYPES:
            raise ValueError("Неподдерживаемый answer type.")
        return "Формулы используют только белый список операций и переменных."

    @staticmethod
    def _check_student_text(draft: dict[str, Any]) -> str:
        text = str(draft.get("candidate_template_text", ""))
        if "{answer}" in text or re.search(r"\bответ\s*[:=]", text, re.IGNORECASE):
            raise ValueError("Ученический текст не должен содержать готовый ответ.")
        return "Ответ отделён от текста для ученика."

    @staticmethod
    def _check_russian(draft: dict[str, Any]) -> str:
        if draft.get("language") != "ru":
            return "Не русский шаблон: проверка русской пунктуации не требуется."
        text = str(draft.get("candidate_template_text", "")).strip()
        if text and text[-1] not in ".?!":
            raise ValueError("Русский текст должен оканчиваться знаком препинания.")
        if "  " in text:
            raise ValueError("В тексте шаблона есть двойные пробелы.")
        grammar = draft.get("grammar_metadata", {})
        if grammar and not isinstance(grammar, dict):
            raise ValueError("Grammar metadata должна быть объектом.")
        validate_slots(text)
        schema = dict(draft.get("parameter_schema", {}))
        schema.update(story_variant_parameters(draft))
        owners = alphabet_owner_names(schema)
        for key, spec in re.findall(r"\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^{}]+?)\s*\}", text):
            kind = schema.get(key, {}).get("type") if isinstance(schema.get(key), dict) else None
            operation = spec.split(",", 1)[0].strip()
            # Владелец вымышленного языка тоже имеет род: «Иван придумал»,
            # «Таня придумала». В схеме его нет — он производное от letter_order.
            if operation == "g" and key in owners:
                continue
            if operation == "g" and kind not in {"character", "noun"}:
                raise ValueError(f"Слот {{{key}:g,...}} требует параметр типа character или noun.")
            if operation == "verb" and kind not in {
                None, "integer", "positive_integer", "nonnegative_integer", "choice",
            }:
                raise ValueError(f"Слот {{{key}:verb,...}} требует числовой параметр или derived-величину.")
            if operation in {"count", "agree"} and kind != "noun":
                raise ValueError(f"Слот {{{key}:{operation},...}} требует параметр типа noun.")
            if operation in {"loc", "dir"} and kind not in {"location", "toponym"}:
                raise ValueError(
                    f"Слот {{{key}:{operation}}} — только для параметра типа location или toponym."
                )
            if operation == "from" and kind != "toponym":
                raise ValueError(f"Слот {{{key}:from}} — только для параметра типа toponym.")
            if operation in {"nom_pl", "gen_pl", "dat_pl", "acc_pl", "ins_pl", "pre_pl"} and kind != "noun":
                # У персонажей и локаций множественного числа в реестре нет.
                raise ValueError(f"Слот {{{key}:{operation}}} (мн. ч.) требует параметр типа noun.")
            if operation in {"one", "two", "three", "one_pl", "two_pl", "three_pl"}:
                if kind != "trait_scale":
                    raise ValueError(
                        f"Слот {{{key}:{operation}}} — только для параметра типа trait_scale."
                    )
                continue
            if operation == "clock" and kind not in {None, "integer", "choice"}:
                # None — величина из derived_values: часы и минуты почти всегда
                # считаются, а не разыгрываются напрямую.
                raise ValueError(
                    f"Слот {{{key}:clock}} — только для числа: целого параметра, "
                    "выбора из списка или производной величины."
                )
            derived_names = set(draft.get("derived_values") or {})
            if (operation not in {"g", "count", "agree", "loc", "dir", "from", "move", "verb",
                                  "speed_phrase", "clock"}
                    and kind not in {"character", "noun", "location", "toponym"}
                    and key not in derived_names):
                raise ValueError(
                    f"Падежный слот {{{key}:{operation}}} требует параметр типа "
                    f"character, noun, location или toponym."
                )
        return "Слоты, роды и падежи согласованы; базовая пунктуация корректна."

    @staticmethod
    def _check_story_profile(draft: dict[str, Any]) -> str:
        """Проверить режим сюжета без привязки к конкретной математике."""
        profile = draft.get("story_profile")
        if not isinstance(profile, dict):
            raise ValueError("story_profile должен быть JSON-объектом.")
        mode = profile.get("mode")
        if mode not in {"universe", "common", "neutral", "abstract"}:
            raise ValueError("story_profile.mode: universe, common, neutral или abstract.")
        if mode == "universe" and profile.get("same_universe") is not True:
            raise ValueError("Сюжет universe обязан содержать same_universe=true.")
        return "Режим сюжета и правило изоляции вселенной корректны."

    @staticmethod
    def _bundle_outputs(schema: dict[str, Any]) -> set[str]:
        """Имена, которые generic bundle раскрывает в набор параметров."""
        result: set[str] = set()
        for rule in schema.values():
            if isinstance(rule, dict) and rule.get("type") == "bundle":
                bind = rule.get("bind", {})
                if isinstance(bind, dict):
                    result.update(value for value in bind.values() if isinstance(value, str))
        return result

    @staticmethod
    def _check_variants(draft: dict[str, Any]) -> str:
        """Проверить ссылки вариантов без привязки к конкретной теме."""
        stories = draft.get("story_variants")
        parameters = draft.get("parameter_variants")
        if stories is None and parameters is None:
            return "Варианты не заданы: используется каноническая формулировка."
        if (not isinstance(stories, list) or not isinstance(parameters, list)
                or not stories or not parameters):
            raise ValueError("story_variants и parameter_variants должны быть непустыми списками.")
        story_ids = [item.get("variant_id") for item in stories if isinstance(item, dict)]
        parameter_ids = [item.get("variant_id") for item in parameters if isinstance(item, dict)]
        if (len(story_ids) != len(stories) or len(set(story_ids)) != len(story_ids)
                or not all(isinstance(item, str) for item in story_ids)):
            raise ValueError("Идентификаторы story_variants должны быть уникальными строками.")
        if (len(parameter_ids) != len(parameters) or len(set(parameter_ids)) != len(parameter_ids)
                or not all(isinstance(item, str) for item in parameter_ids)):
            raise ValueError("Идентификаторы parameter_variants должны быть уникальными строками.")
        if "canonical" not in story_ids or "canonical" not in parameter_ids:
            raise ValueError("Канонические story_variant и parameter_variant обязательны.")
        known = set(parameter_ids)
        for story in stories:
            supported = story.get("supported_parameter_variants", list(known))
            if not isinstance(supported, list) or not supported or set(supported) - known:
                raise ValueError("У story_variant должны быть существующие supported_parameter_variants.")
            text = story.get("text", story.get("candidate_template_text"))
            if text is not None and (not isinstance(text, str) or not text.strip()):
                raise ValueError("Текст story_variant должен быть непустой строкой.")
            TemplateStudioService._check_variant_text(draft, story, text)
        return f"Варианты корректны: {len(stories)} сюжетных × {len(parameters)} параметрических."

    @staticmethod
    def _check_variant_text(draft: dict[str, Any], story: dict[str, Any], text: Any) -> None:
        """Проверить текст сюжетного варианта так же строго, как канонический.

        Без этого вариант оставался слепой зоной: слоты в нём никто не разбирал,
        и опечатка в имени параметра всплывала только у ребёнка на листочке.
        Каждый вариант проверяется в своей схеме — со своими добавленными
        и убранными параметрами.
        """
        if not isinstance(text, str):
            return
        validate_slots(text)
        if text.strip() and text.strip()[-1] not in ".?!":
            raise ValueError(f"Текст story_variant {story['variant_id']} без знака в конце.")
        if "  " in text:
            raise ValueError(f"В тексте story_variant {story['variant_id']} двойные пробелы.")
        schema = dict(draft.get("parameter_schema", {}))
        for name in story.get("drop_parameters") or ():
            schema.pop(name, None)
        schema.update(story.get("add_parameters") or {})
        for name, rule in schema.items():
            if not isinstance(rule, dict) or rule.get("type") not in SUPPORTED_PARAMETER_TYPES:
                raise ValueError(f"Сюжетный вариант {story['variant_id']}: параметр {name} без типа.")
        defined = (set(schema) | set(draft.get("derived_values", {}))
                   | alphabet_derived_names(schema) | digit_selection_names(schema)
                   | range_count_names(schema) | factor_pair_names(schema)
                   | clock_search_names(schema) | calendar_names(schema)
                   | star_addition_names(schema) | reachability_names(schema)
                   | search_puzzle_names(schema) | max_digit_sum_names(schema)
                   | restoration_names(schema))
        for rule in schema.values():
            if isinstance(rule, dict) and rule.get("type") == "bundle":
                defined |= set(rule.get("bind", {}).values())
        missing = slot_keys(text) - defined
        if missing:
            raise ValueError(
                f"Сюжетный вариант {story['variant_id']}: не определены "
                f"плейсхолдеры {', '.join(sorted(missing))}."
            )

    @staticmethod
    def _expression_variables(draft: dict[str, Any]) -> set[str]:
        derived = " ".join(str(value) for value in draft.get("derived_values", {}).values())
        # Ограничения тоже считаются использованием: параметр, который нужен
        # только чтобы отбраковать негодный жребий, не лишний. Без этого
        # валидатор объявлял такой параметр неиспользуемым.
        constraints = " ".join(str(item) for item in normalize_constraints(
            draft.get("constraints")))
        references = " ".join((derived, constraints, str(draft.get("answer_expression", ""))))
        return set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", references))

    @staticmethod
    def _active_payload(draft: dict[str, Any]) -> dict[str, Any]:
        # constraints обязаны попадать в активный шаблон: без них сайт сгенерирует
        # набор чисел, который автор шаблона считал недопустимым.
        fields = (
            "template_id", "module_id", "candidate_template_text", "parameter_schema",
            "derived_values", "constraints", "answer_expression", "answer_type",
            "answer_rendering", "grammar_metadata", "source_metadata", "solver_strategy",
            "story_profile", "story_variants", "parameter_variants", "abstract_story_exemption",
            "structure_signature", "principal_operation",
        )
        return {field: deepcopy(draft[field]) for field in fields if field in draft} | {
            "activated_at": utc_now(), "studio_draft_id": draft["draft_id"],
        }

    def _event(self, draft: dict[str, Any], action: str, *, details: dict[str, Any] | None = None) -> None:
        event = {"at": utc_now(), "action": action, "details": details or {}}
        draft.setdefault("revision_history", []).append(event)
        draft["updated_at"] = event["at"]
        self.store.append_history(draft["draft_id"], event)

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str) or len(value) > 1000:
            raise ValueError("Метаданные источника должны быть строкой до 1000 символов.")
        return value
