"""Прикладной сервис состояний, проверки и публикации Template Studio."""

from __future__ import annotations

import re
import uuid
from copy import deepcopy
from typing import Any

from .analyzer import TemplateAnalyzer
from .runtime import (
    PLACEHOLDER_RE,
    SUPPORTED_ANSWER_TYPES,
    SUPPORTED_PARAMETER_TYPES,
    TemplateRuntimeError,
    answer_type_matches,
    derive_values,
    generate_active_template,
    normalize_value,
    render_template,
    sample_parameters,
)
from .safe_expressions import SafeExpressionError, evaluate_expression, validate_expression
from .storage import TemplateStudioStore, utc_now


TEMPLATE_ID_RE = re.compile(r"[a-z][a-z0-9_]{2,80}\Z")
EDITABLE_FIELDS = frozenset({
    "template_id", "module_id", "candidate_template_text", "answer_type", "parameter_schema",
    "derived_values", "constraints", "solver_strategy", "answer_expression", "answer_rendering",
    "grammar_metadata", "source_metadata", "notes", "language",
})
KNOWN_STRATEGIES = frozenset({"formula", "manual"})


class TemplateStudioService:
    """Сервис хранит все переходы статусов и не публикует непроверенные drafts."""

    def __init__(self, store: TemplateStudioStore | None = None, analyzer: TemplateAnalyzer | None = None) -> None:
        self.store = store or TemplateStudioStore()
        self.analyzer = analyzer or TemplateAnalyzer()

    def create_from_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
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
        self._event(draft, "analysis_run", details={"warnings": analysis["warnings"], "unsupported_features": analysis["unsupported_features"]})
        return self.store.save_draft(draft)

    def update_draft(self, draft_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        draft = self.store.load_draft(draft_id)
        if draft["status"] not in {"draft", "validated"}:
            raise ValueError("Редактировать можно только черновик или validated-шаблон.")
        unknown = set(changes) - EDITABLE_FIELDS
        if unknown:
            raise ValueError(f"Нельзя редактировать системные поля: {', '.join(sorted(unknown))}.")
        for field, value in changes.items():
            if field in {"template_id", "candidate_template_text", "answer_type", "solver_strategy", "answer_expression", "language", "notes"} and not isinstance(value, str):
                raise ValueError(f"Поле {field} должно быть строкой.")
            if field in {"parameter_schema", "derived_values", "constraints", "answer_rendering", "grammar_metadata", "source_metadata"} and not isinstance(value, dict):
                raise ValueError(f"Поле {field} должно быть JSON-объектом.")
            if field == "module_id" and value is not None and not isinstance(value, str):
                raise ValueError("module_id должен быть строкой или null.")
            draft[field] = deepcopy(value)
        draft["status"] = "draft"
        draft["validation_report"] = None
        self._event(draft, "draft_edited", details={"fields": sorted(changes)})
        return self.store.save_draft(draft)

    def preview(self, draft_id: str, *, count: int = 3, seed: int = 1) -> dict[str, Any]:
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
                    "derived_values": {name: normalize_value(values[name]) for name in draft["derived_values"]},
                    "answer": generated["answer"],
                    "validation": {"passed": True, "message": "Экземпляр сгенерирован."},
                })
            except (TemplateRuntimeError, SafeExpressionError, ValueError) as error:
                previews.append({"seed": preview_seed, "rendered_problem": None, "parameters": {}, "derived_values": {}, "answer": None, "validation": {"passed": False, "message": str(error)}})
        self._event(draft, "preview_generated", details={"count": count, "seed": seed})
        self.store.save_draft(draft)
        return {"draft_id": draft_id, "previews": previews}

    def validate(self, draft_id: str, *, known_module_ids: set[str], existing_template_ids: set[str]) -> dict[str, Any]:
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
        check("template_id", "Уникальный template ID", lambda: self._check_template_id(draft, existing_template_ids))
        check("module", "Известный модуль", lambda: self._check_module(draft, known_module_ids))
        check("strategy", "Поддерживаемая стратегия", lambda: self._check_strategy(draft))
        check("placeholders", "Плейсхолдеры определены", lambda: self._check_placeholders(draft))
        check("parameters", "Ограниченная схема параметров", lambda: self._check_parameters(draft))
        check("expressions", "Безопасные derived- и answer-выражения", lambda: self._check_expressions(draft))
        check("student_text", "Текст для ученика не раскрывает ответ", lambda: self._check_student_text(draft))
        check("russian", "Базовая русская пунктуация и метаданные", lambda: self._check_russian(draft))
        examples = self._validate_examples(draft, checks)
        passed = all(item["passed"] for item in checks)
        report = {"draft_id": draft_id, "validated_at": utc_now(), "passed": passed, "checks": checks, "successful_examples": examples}
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

    def activate(self, draft_id: str, *, known_module_ids: set[str], existing_template_ids: set[str]) -> dict[str, Any]:
        draft = self.store.load_draft(draft_id)
        if draft["status"] != "validated" or not draft.get("validation_report", {}).get("passed"):
            raise ValueError("Активировать можно только успешно validated-шаблон.")
        self._check_module(draft, known_module_ids)
        self._check_template_id(draft, existing_template_ids | {item.get("template_id", "") for item in self.store.load_active_templates()})
        active_template = self._active_payload(draft)
        self.store.activate(active_template)
        draft["status"] = "active"
        self._event(draft, "activated", details={"module_id": draft["module_id"], "template_id": draft["template_id"]})
        return self.store.save_draft(draft)

    def archive(self, draft_id: str) -> dict[str, Any]:
        draft = self.store.load_draft(draft_id)
        if draft["status"] != "active":
            raise ValueError("Архивировать можно только active-шаблон.")
        self.store.archive_active(draft["template_id"])
        draft["status"] = "archived"
        self._event(draft, "archived")
        return self.store.save_draft(draft)

    def restore(self, draft_id: str, *, known_module_ids: set[str], existing_template_ids: set[str]) -> dict[str, Any]:
        draft = self.store.load_draft(draft_id)
        if draft["status"] != "archived":
            raise ValueError("Восстановить можно только archived-шаблон.")
        report = self.validate(draft_id, known_module_ids=known_module_ids, existing_template_ids=existing_template_ids)
        if not report["passed"]:
            raise ValueError("Восстановление остановлено: шаблон не прошёл текущую валидацию.")
        restored = self.activate(draft_id, known_module_ids=known_module_ids, existing_template_ids=existing_template_ids)
        self._event(restored, "restored")
        return self.store.save_draft(restored)

    def reject(self, draft_id: str, reason: str) -> dict[str, Any]:
        draft = self.store.load_draft(draft_id)
        if draft["status"] not in {"draft", "validated"}:
            raise ValueError("Отклонить можно только draft или validated-шаблон.")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
            raise ValueError("Укажите причину отклонения не длиннее 1000 символов.")
        draft["status"] = "rejected"
        self._event(draft, "rejected", details={"reason": reason.strip()})
        return self.store.save_draft(draft)

    def delete_draft(self, draft_id: str, *, confirmed: bool) -> None:
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
        answer_type = draft.get("answer_type")
        for seed in range(10):
            try:
                generated = generate_active_template(draft, random.Random(seed))
                independent = evaluate_expression(draft["answer_expression"], generated["parameters"])
                normalized_independent = normalize_value(independent)
                if generated["answer"] != normalized_independent:
                    raise ValueError("Независимый расчёт не совпал с ответом шаблона.")
                if not answer_type_matches(normalized_independent, answer_type):
                    raise ValueError(f"Ответ не соответствует типу {answer_type}.")
                successful += 1
            except (ValueError, TemplateRuntimeError, SafeExpressionError) as error:
                checks.append({"id": "examples", "label": "Детерминированные примеры и независимый расчёт", "passed": False, "message": f"seed {seed}: {error}"})
                return successful
        checks.append({"id": "examples", "label": "Детерминированные примеры и независимый расчёт", "passed": True, "message": f"Проверено {successful} seed."})
        return successful

    @staticmethod
    def _check_schema(draft: dict[str, Any]) -> str:
        required = {"draft_id", "status", "original_text", "candidate_template_text", "parameter_schema", "derived_values", "answer_expression"}
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
        placeholders = set(PLACEHOLDER_RE.findall(text))
        invalid = re.findall(r"\{([^{}]+)\}", text)
        for value in invalid:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
                raise ValueError(f"Недопустимый плейсхолдер {{{value}}}.")
        defined = set(draft.get("parameter_schema", {})) | set(draft.get("derived_values", {}))
        missing = placeholders - defined
        if missing:
            raise ValueError(f"Не определены плейсхолдеры: {', '.join(sorted(missing))}.")
        unused = set(draft.get("parameter_schema", {})) - (placeholders | cls._expression_variables(draft))
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
        sample_parameters(schema, __import__("random").Random(0))
        return "Типы параметров и границы генерации корректны."

    @staticmethod
    def _check_expressions(draft: dict[str, Any]) -> str:
        variables = set(draft["parameter_schema"])
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
        grammar = draft.get("grammar_metadata", {})
        if grammar and not isinstance(grammar, dict):
            raise ValueError("Grammar metadata должна быть объектом.")
        return "Плейсхолдеры неразрешёнными не остаются; базовая пунктуация корректна."

    @staticmethod
    def _expression_variables(draft: dict[str, Any]) -> set[str]:
        references = " ".join(str(value) for value in draft.get("derived_values", {}).values()) + " " + str(draft.get("answer_expression", ""))
        return set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", references))

    @staticmethod
    def _active_payload(draft: dict[str, Any]) -> dict[str, Any]:
        fields = ("template_id", "module_id", "candidate_template_text", "parameter_schema", "derived_values", "answer_expression", "answer_type", "answer_rendering", "grammar_metadata", "source_metadata", "solver_strategy")
        return {field: deepcopy(draft[field]) for field in fields} | {"activated_at": utc_now(), "studio_draft_id": draft["draft_id"]}

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
