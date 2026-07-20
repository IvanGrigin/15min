"""Provider-candidate → strict JSON draft → validation → active overlay."""

from __future__ import annotations

import json
import random
import re
import uuid
from copy import deepcopy
from typing import Any

from problemgen.template_studio.runtime import (
    SUPPORTED_PARAMETER_TYPES, TemplateRuntimeError, answer_type_matches,
    generate_active_template, normalize_value,
)
from problemgen.template_studio.safe_expressions import SafeExpressionError, expression_names, evaluate_expression, validate_expression
from problemgen.template_studio.storage import TemplateStudioStore, utc_now

from .provider import MathTemplateGenerationProvider, ProviderError
from .storage import TemplateCreatorStore


SUPPORTED_CREATOR_ANSWER_TYPES = frozenset({
    "integer", "decimal", "fraction", "boolean", "word", "word_list", "integer_list",
    "ordered_list", "multi_part", "cryptarithm_solutions",
})
_ID_RE = re.compile(r"[a-z][a-z0-9_]{2,80}\Z")


class TemplateCreatorService:
    """Не доверяет provider JSON: публикация возможна только после проверки."""

    def __init__(self, provider: MathTemplateGenerationProvider | None, *, store: TemplateCreatorStore | None = None, active_store: TemplateStudioStore | None = None) -> None:
        self.provider = provider
        self.store = store or TemplateCreatorStore()
        self.active_store = active_store or TemplateStudioStore()

    def generate(self, problem_text: str, module_id: str | None, context: dict[str, Any]) -> dict[str, Any]:
        self._check_problem(problem_text)
        if self.provider is None:
            raise ValueError("Автоматический генератор шаблонов не настроен.")
        candidate, report, previews, repair_attempts = self._generate_with_repairs(problem_text, module_id, context)
        now = utc_now()
        draft = {
            "schema_version": 1, "draft_id": f"creator_{uuid.uuid4().hex}", "status": "valid" if report["passed"] else "draft",
            "created_at": now, "updated_at": now, "original_problem": problem_text, "generated_json": candidate,
            "provider_metadata": {"provider": type(self.provider).__name__}, "repair_attempts": repair_attempts,
            "validation_report": report, "preview_results": previews, "revision_history": [{"at": now, "action": "generated"}],
        }
        self.store.save_report(draft["draft_id"], report)
        self.store.append_history(draft["draft_id"], draft["revision_history"][0])
        return self.store.save_creator_draft(draft)

    def regenerate(self, draft_id: str, context: dict[str, Any]) -> dict[str, Any]:
        old = self.store.load_draft(draft_id)
        if self.provider is None:
            raise ValueError("Автоматический генератор шаблонов не настроен.")
        candidate, report, previews, attempts = self._generate_with_repairs(old["original_problem"], old["generated_json"].get("module_id"), context)
        old["revision_history"].append({"at": utc_now(), "action": "regenerated", "previous_generated_json": old["generated_json"]})
        old.update({"generated_json": candidate, "validation_report": report, "preview_results": previews, "repair_attempts": attempts, "status": "valid" if report["passed"] else "draft", "updated_at": utc_now()})
        self.store.save_report(draft_id, report)
        self.store.append_history(draft_id, old["revision_history"][-1])
        return self.store.save_creator_draft(old)

    def validate(self, draft_id: str, context: dict[str, Any]) -> dict[str, Any]:
        draft = self.store.load_draft(draft_id)
        report = self._validate_candidate(draft["generated_json"], context)
        draft["validation_report"] = report
        draft["preview_results"] = self._previews(draft["generated_json"], report)
        draft["status"] = "valid" if report["passed"] else "draft"
        draft["updated_at"] = utc_now()
        draft["revision_history"].append({"at": draft["updated_at"], "action": "validated"})
        self.store.save_report(draft_id, report)
        return self.store.save_creator_draft(draft)

    def activate(self, draft_id: str, context: dict[str, Any]) -> dict[str, Any]:
        draft = self.validate(draft_id, context)
        if not draft["validation_report"]["passed"]:
            raise ValueError("Добавление в список отключено: JSON-шаблон не прошёл проверку.")
        candidate = draft["generated_json"]
        if candidate.get("activation_blocked"):
            raise ValueError(str(candidate.get("unsupported_reason") or "Активация этого типа задачи заблокирована."))
        active_ids = {item.get("template_id") for item in self.active_store.load_active_templates()}
        if candidate["template_id"] in active_ids or candidate["template_id"] in context["existing_template_ids"]:
            raise ValueError("template_id уже существует.")
        self.active_store.activate(self._active_payload(candidate))
        draft["status"] = "active"
        draft["updated_at"] = utc_now()
        draft["revision_history"].append({"at": draft["updated_at"], "action": "activated"})
        return self.store.save_creator_draft(draft)

    def delete(self, draft_id: str, *, confirmed: bool) -> None:
        if not confirmed:
            raise ValueError("Удаление требует подтверждения.")
        draft = self.store.load_draft(draft_id)
        if draft.get("status") == "active":
            raise ValueError("Активный шаблон нельзя удалить: используйте archive workflow.")
        self.store.append_history(draft_id, {"at": utc_now(), "action": "deleted"})
        self.store.delete_draft_file(draft_id)
        (self.store.reports_root / f"{draft_id}.json").unlink(missing_ok=True)

    def _generate_with_repairs(self, text: str, module_id: str | None, context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], int]:
        errors: list[str] | None = None
        candidate: dict[str, Any] = {}
        report: dict[str, Any] = {"passed": False, "checks": []}
        for attempt in range(4):
            candidate = self._normalize_candidate(self.provider.generate_template(text, context, repair_errors=errors), text, module_id)
            report = self._validate_candidate(candidate, context)
            if report["passed"]:
                return candidate, report, self._previews(candidate, report), attempt
            errors = [item["message"] for item in report["checks"] if not item["passed"]]
        return candidate, report, self._previews(candidate, report), 3

    def _normalize_candidate(self, raw: dict[str, Any], original: str, selected_module: str | None) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise ProviderError("Провайдер должен вернуть JSON-объект.")
        try:
            serialized = json.dumps(raw, ensure_ascii=False)
        except (TypeError, ValueError) as error:
            raise ProviderError("Провайдер вернул не JSON-совместимый объект.") from error
        if len(serialized) > 65_536 or self._json_depth(raw) > 12:
            raise ProviderError("Ответ провайдера превышает разрешённый размер или глубину JSON.")
        provider_schema_errors = self._provider_shape_errors(raw)
        family = str(raw.get("family", "unsupported"))
        module = selected_module or raw.get("module_suggestion") or raw.get("module_id")
        template_id = str(raw.get("template_id") or f"{family}_generated_{uuid.uuid4().hex[:8]}").lower()
        derived = raw.get("derived", {})
        return {
            "template_id": template_id, "module_id": module, "status": "draft", "source_type": "automatic",
            "original_problem": original, "family": family, "strategy": raw.get("strategy_suggestion", raw.get("strategy", "formula")),
            "answer_type": raw.get("answer_type", "integer"), "template_text": raw.get("template_text", ""),
            "parameters": raw.get("parameters", {}), "derived": derived, "constraints": raw.get("constraints", []),
            "grammar": raw.get("grammar", {"language": "ru"}), "source_problem_numbers": [],
            "generation_notes": raw.get("generation_notes", []), "warnings": raw.get("warnings", []),
            "confidence": raw.get("confidence", {}), "solver_description": raw.get("solver_description", ""),
            "activation_blocked": bool(raw.get("activation_blocked", False)), "unsupported_reason": raw.get("unsupported_reason"),
            "provider_schema_errors": provider_schema_errors,
        }

    def _validate_candidate(self, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        def check(identifier: str, action: Any) -> None:
            try: checks.append({"id": identifier, "passed": True, "message": action() or "OK"})
            except (ValueError, TypeError, SafeExpressionError, TemplateRuntimeError) as error: checks.append({"id": identifier, "passed": False, "message": str(error)})
        check("schema", lambda: self._check_schema(candidate, context))
        check("expressions", lambda: self._check_expressions(candidate))
        check("generation", lambda: self._check_generation(candidate))
        check("independent_answer", lambda: self._check_independent_answer(candidate))
        return {"passed": all(item["passed"] for item in checks), "checks": checks, "validated_at": utc_now()}

    @staticmethod
    def _check_schema(c: dict[str, Any], context: dict[str, Any]) -> str:
        if c.get("provider_schema_errors"):
            raise ValueError("Провайдер нарушил intermediate schema: " + "; ".join(c["provider_schema_errors"]))
        required = {"template_id", "module_id", "family", "template_text", "parameters", "derived", "answer_type", "strategy", "grammar"}
        missing = required - set(c)
        if missing: raise ValueError(f"Отсутствуют поля: {', '.join(sorted(missing))}.")
        if not _ID_RE.fullmatch(str(c["template_id"])): raise ValueError("Некорректный template_id.")
        if c["module_id"] not in context["module_ids"]: raise ValueError("Неизвестный target module.")
        if c["answer_type"] not in SUPPORTED_CREATOR_ANSWER_TYPES: raise ValueError("Неподдерживаемый answer type.")
        if c["strategy"] != "formula": raise ValueError("strategy_implementation_required: стратегия не реализована безопасно.")
        if not isinstance(c["parameters"], dict) or not c["parameters"]: raise ValueError("Нужны bounded independent parameters.")
        if not isinstance(c["grammar"], dict) or c["grammar"].get("language") != "ru": raise ValueError("Нужны Russian grammar metadata с language=ru.")
        name_parameters = [name for name, rule in c["parameters"].items() if isinstance(rule, dict) and rule.get("type") == "name"]
        if name_parameters:
            name_roles = c["grammar"].get("name_roles")
            if not isinstance(name_roles, dict): raise ValueError("Для имён нужны grammar.name_roles без эвристического склонения.")
            for name in name_parameters:
                metadata = name_roles.get(name)
                if not isinstance(metadata, dict) or metadata.get("gender") not in {"male", "female", "any"} or not isinstance(metadata.get("required_forms"), list):
                    raise ValueError(f"Для имени {name} не заданы род и required_forms.")
        return "Строгая JSON-схема и каталог корректны."

    @staticmethod
    def _check_expressions(c: dict[str, Any]) -> str:
        variables = set(c["parameters"])
        for name, rule in c["parameters"].items():
            if not isinstance(rule, dict) or rule.get("type") not in SUPPORTED_PARAMETER_TYPES: raise ValueError(f"Неизвестный тип {name}.")
            if rule.get("type") in {"integer", "positive_integer", "nonnegative_integer", "decimal", "fraction"} and ("minimum" not in rule or "maximum" not in rule): raise ValueError(f"Нет границ {name}.")
        derived = dict(c["derived"])
        used_names = set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", c["template_text"]))
        while derived:
            progressed = False
            for name, expression in list(derived.items()):
                try: validate_expression(str(expression), variables)
                except SafeExpressionError as error:
                    if "Неизвестная переменная" in str(error): continue
                    raise ValueError(str(error)) from error
                used_names.update(expression_names(str(expression)) - {"abs", "min", "max", "sum", "gcd", "lcm", "factorial"})
                variables.add(name); del derived[name]; progressed = True
            if not progressed: raise ValueError("Цикл или неизвестная переменная в derived.")
        if "answer" not in c["derived"]: raise ValueError("Derived answer formula обязательна.")
        placeholders = set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", c["template_text"]))
        if placeholders - variables: raise ValueError("В тексте есть неописанный плейсхолдер.")
        unused = set(c["parameters"]) - used_names
        if unused: raise ValueError(f"Неиспользуемые независимые параметры: {', '.join(sorted(unused))}.")
        return "Выражения ограничены безопасным AST и все плейсхолдеры определены."

    @staticmethod
    def _as_runtime(c: dict[str, Any]) -> dict[str, Any]:
        derived = dict(c["derived"]); answer = derived.pop("answer")
        return {"candidate_template_text": c["template_text"], "parameter_schema": c["parameters"], "derived_values": derived, "answer_expression": answer, "answer_type": c["answer_type"]}

    def _check_generation(self, c: dict[str, Any]) -> str:
        runtime = self._as_runtime(c)
        for seed in range(3):
            generated = generate_active_template(runtime, random.Random(seed))
            if not answer_type_matches(generated["answer"], c["answer_type"]):
                raise ValueError(f"Ответ не соответствует declared type {c['answer_type']}.")
        return "Три deterministic preview генерируются без ошибок."

    def _check_independent_answer(self, c: dict[str, Any]) -> str:
        if c["family"] != "arithmetic_sequence_sum":
            if c.get("activation_blocked"):
                return "Независимый solver отсутствует; активация корректно заблокирована."
            raise ValueError("strategy_implementation_required: нет независимого solver для family.")
        runtime = self._as_runtime(c)
        for seed in range(3):
            generated = generate_active_template(runtime, random.Random(seed)); p = generated["parameters"]
            independent = sum(p["first_term"] + p["difference"] * index for index in range(p["term_count"]))
            if generated["answer"] != independent: raise ValueError("Независимая сумма членов не совпала с answer.")
        return "Ответ независимо проверен явным суммированием членов."

    def _previews(self, c: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
        if not report.get("passed"): return []
        runtime = self._as_runtime(c); previews=[]
        for seed in range(3):
            g=generate_active_template(runtime, random.Random(seed)); names=set(c["parameters"])
            previews.append({"seed": seed, "rendered_problem": g["rendered_problem"], "parameters": {k: normalize_value(v) for k,v in g["parameters"].items() if k in names}, "derived_values": {k: normalize_value(v) for k,v in g["parameters"].items() if k not in names}, "answer": g["answer"], "validation": "passed"})
        return previews

    @staticmethod
    def _active_payload(c: dict[str, Any]) -> dict[str, Any]:
        derived=dict(c["derived"]); answer=derived.pop("answer")
        return {"template_id":c["template_id"],"module_id":c["module_id"],"candidate_template_text":c["template_text"],"parameter_schema":c["parameters"],"derived_values":derived,"answer_expression":answer,"answer_type":c["answer_type"],"answer_rendering":{"type":c["answer_type"]},"grammar_metadata":c["grammar"],"source_metadata":{"problem_number":None},"solver_strategy":"formula","activated_at":utc_now()}

    @staticmethod
    def _check_problem(text: str) -> None:
        if not isinstance(text, str) or not text.strip() or len(text) > 20_000: raise ValueError("Задача должна быть непустым текстом до 20000 символов.")

    @staticmethod
    def _json_depth(value: Any) -> int:
        if isinstance(value, dict): return 1 + max((TemplateCreatorService._json_depth(item) for item in value.values()), default=0)
        if isinstance(value, list): return 1 + max((TemplateCreatorService._json_depth(item) for item in value), default=0)
        return 0

    @staticmethod
    def _provider_shape_errors(raw: dict[str, Any]) -> list[str]:
        """Минимальная строгая проверка до normalisation без зависимости от jsonschema."""
        expected = {
            "family": str, "module_suggestion": str, "template_text": str,
            "parameters": dict, "derived": dict, "answer_type": str,
            "strategy_suggestion": str, "grammar": dict,
        }
        errors = [f"нет поля {name}" for name in expected if name not in raw]
        errors.extend(f"поле {name} имеет неверный тип" for name, kind in expected.items() if name in raw and not isinstance(raw[name], kind))
        if "constraints" in raw and not isinstance(raw["constraints"], list): errors.append("constraints должен быть массивом")
        if "warnings" in raw and not isinstance(raw["warnings"], list): errors.append("warnings должен быть массивом")
        if "confidence" in raw and not isinstance(raw["confidence"], dict): errors.append("confidence должен быть объектом")
        return errors
