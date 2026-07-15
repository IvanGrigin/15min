from __future__ import annotations

import copy
import json
import random
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from problemgen.source_index.answer_definition_cleanup import (
    discover_supported_answer_types,
    evaluate_formula,
    type_matches,
    validate_answer_definition,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates.json"
REJECTED_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_rejected.json"
ANSWER_RECOVERY_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_answer_recovery.json"

NUMBER_PLACEHOLDER_RE = re.compile(r"{(number_([1-9]\d*))}")
ANY_PLACEHOLDER_RE = re.compile(r"{([^}]+)}")
MAX_ATTEMPTS = 500


@dataclass(frozen=True)
class EligibilityResult:
    eligible: list[dict[str, Any]]
    excluded: list[dict[str, Any]]
    stats: dict[str, int]
    supported_answer_types: list[str]


def load_template_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rejected_template_ids(path: Path = REJECTED_PATH) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for record in payload.get("rejected_templates", []):
        template_id = record.get("template_id")
        if isinstance(template_id, str):
            ids.add(template_id)
    return ids


def load_answer_recoveries(path: Path = ANSWER_RECOVERY_PATH) -> list[dict[str, Any]]:
    """Load the reviewed answer-formula overlay without mutating the archive."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    recoveries = payload.get("recoveries", [])
    if not isinstance(recoveries, list):
        raise ValueError("all_tasks_answer_recovery.json must contain a 'recoveries' list.")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for recovery in recoveries:
        if not isinstance(recovery, dict):
            raise ValueError("Each answer recovery must be an object.")
        template_id = recovery.get("template_id")
        answer_type = recovery.get("answer_type")
        formula = recovery.get("answer_formula")
        if not isinstance(template_id, str) or not template_id.strip():
            raise ValueError("Each answer recovery needs a template_id.")
        if template_id in seen:
            raise ValueError(f"Duplicate answer recovery for {template_id}.")
        if not isinstance(answer_type, str) or not answer_type.strip():
            raise ValueError(f"Answer recovery {template_id} needs answer_type.")
        if not isinstance(formula, str) or not formula.strip():
            raise ValueError(f"Answer recovery {template_id} needs answer_formula.")
        seen.add(template_id)
        normalized.append(copy.deepcopy(recovery))
    return normalized


def catalog_with_recovered_answers(
    catalog: dict[str, Any] | None = None,
    recoveries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a catalog copy enriched only with explicit reviewed formulas."""
    source = copy.deepcopy(catalog if catalog is not None else load_template_catalog())
    templates = source.get("templates", [])
    if not isinstance(templates, list):
        raise ValueError("all_tasks_templates.json must contain a 'templates' list.")
    recovery_records = recoveries if recoveries is not None else load_answer_recoveries()
    by_id = {template.get("template_id"): template for template in templates}
    for recovery in recovery_records:
        template_id = recovery["template_id"]
        template = by_id.get(template_id)
        if not isinstance(template, dict):
            raise ValueError(f"Answer recovery references unknown template {template_id}.")
        expected_number = recovery.get("template_number")
        if expected_number is not None and template.get("template_number") != expected_number:
            raise ValueError(f"Answer recovery number does not match template {template_id}.")
        template["answer_type"] = recovery["answer_type"]
        template["answer_formula"] = recovery["answer_formula"]
        template["answer_recovery"] = {
            "source_answer": recovery.get("source_answer"),
            "verification": recovery.get("verification"),
        }
    return source


def recovered_templates() -> list[dict[str, Any]]:
    """Return only archive templates that now have a reviewed computable answer."""
    recoveries = load_answer_recoveries()
    recovered_ids = {recovery["template_id"] for recovery in recoveries}
    result = filter_eligible_templates(catalog_with_recovered_answers(recoveries=recoveries))
    templates = [template for template in result.eligible if template.get("template_id") in recovered_ids]
    if len(templates) != len(recovered_ids):
        available = {template.get("template_id") for template in templates}
        missing = ", ".join(sorted(recovered_ids - available))
        raise ValueError(f"Recovered templates are not safely generatable: {missing}.")
    for template in templates:
        recovery = template.get("answer_recovery", {})
        expected_answer = recovery.get("source_answer") if isinstance(recovery, dict) else None
        if expected_answer is not None:
            source_answer = evaluate_formula(str(template["answer_formula"]), template)
            if source_answer != expected_answer:
                raise ValueError(f"Source-answer check failed for {template.get('template_id')}.")
    return templates


def unverified_templates() -> list[dict[str, Any]]:
    """Return archive records that remain deliberately unavailable as answered tasks."""
    recovered_ids = {recovery["template_id"] for recovery in load_answer_recoveries()}
    return [template for template in filter_eligible_templates().eligible if template.get("template_id") not in recovered_ids]


def recovery_stats() -> dict[str, int]:
    """Report the reviewed and still-unreviewed parts of the archive."""
    return {
        "recovered_templates": len(recovered_templates()),
        "unverified_templates": len(unverified_templates()),
    }


def number_placeholder_names(template_text: str) -> list[str]:
    seen: dict[str, None] = {}
    for match in NUMBER_PLACEHOLDER_RE.finditer(template_text):
        seen.setdefault(match.group(1), None)
    return sorted(seen, key=lambda name: int(name.split("_", 1)[1]))


def has_only_number_placeholders(template_text: str) -> bool:
    return all(name.startswith("number_") and name[7:].isdigit() and not name.startswith("number_0") for name in ANY_PLACEHOLDER_RE.findall(template_text))


def display_name(template: dict[str, Any]) -> str | None:
    title = str(template.get("title") or "").strip()
    module_name = str(template.get("module_name") or "").strip()
    number = template.get("template_number")
    if title:
        return f"{title} — шаблон №{number}"
    if module_name:
        return f"{module_name} — шаблон №{number}"
    return None


def _is_missing_formula(template: dict[str, Any]) -> bool:
    formula = template.get("answer_formula")
    return not isinstance(formula, str) or not formula.strip()


def filter_eligible_templates(
    catalog: dict[str, Any] | None = None,
    rejected_ids: set[str] | None = None,
) -> EligibilityResult:
    if catalog is None:
        catalog = load_template_catalog()
    if rejected_ids is None:
        rejected_ids = load_rejected_template_ids()
    templates = catalog.get("templates", [])
    if not isinstance(templates, list):
        templates = []

    supported_answer_types = discover_supported_answer_types(templates)
    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    stats = {
        "total_templates": len(templates),
        "eligible_templates": 0,
        "excluded_templates": 0,
        "excluded_rejected": 0,
        "excluded_forbidden_placeholders": 0,
        "excluded_missing_display_name": 0,
        "excluded_invalid_formulas": 0,
        "excluded_unsupported_answer_types": 0,
        "excluded_missing_safe_generators": 0,
        "excluded_integer_answer": 0,
        "excluded_grammar": 0,
        "selectable_without_answer_formula": 0,
    }

    for template in templates:
        reason = template_exclusion_reason(template, rejected_ids, supported_answer_types)
        if reason is None:
            enriched = copy.deepcopy(template)
            enriched["display_name"] = display_name(template)
            if uses_source_values_fallback(enriched):
                enriched["generation_mode"] = "source_values_fallback"
                stats["selectable_without_answer_formula"] += 1
            else:
                enriched["generation_mode"] = "validated_integer_answer"
            eligible.append(enriched)
            continue
        excluded.append({
            "template_id": template.get("template_id"),
            "template_number": template.get("template_number"),
            "reason_code": reason,
        })
        stats["excluded_templates"] += 1
        if reason in stats:
            stats[reason] += 1

    stats["eligible_templates"] = len(eligible)
    return EligibilityResult(eligible, excluded, stats, sorted(supported_answer_types))


def template_exclusion_reason(
    template: dict[str, Any],
    rejected_ids: set[str],
    supported_answer_types: set[str],
) -> str | None:
    template_id = template.get("template_id")
    if isinstance(template_id, str) and template_id in rejected_ids:
        return "excluded_rejected"
    template_text = template.get("template_text")
    if not isinstance(template_text, str) or not template_text.strip():
        return "excluded_forbidden_placeholders"
    if display_name(template) is None:
        return "excluded_missing_display_name"
    if not has_only_number_placeholders(template_text):
        return "excluded_forbidden_placeholders"
    if uses_source_values_fallback(template):
        return None
    answer_type = template.get("answer_type")
    if not isinstance(answer_type, str) or answer_type.strip().lower() in {"", "unknown", "undefined", "todo", "pending", "none", "null", "n/a"}:
        return "excluded_unsupported_answer_types"
    if _is_missing_formula(template):
        return "excluded_invalid_formulas"
    valid, reason_code, _ = validate_answer_definition(template, supported_answer_types)
    if not valid:
        if reason_code in {"invalid_answer_type", "missing_answer_type", "missing_answer_definition"}:
            return "excluded_unsupported_answer_types"
        if reason_code in {"missing_answer_formula", "invalid_answer_formula", "undefined_formula_placeholders", "formula_execution_error"}:
            return "excluded_invalid_formulas"
        return "excluded_missing_safe_generators"
    try:
        generated = generate_problem_instance(template, random.Random(1), require_changed=False, max_attempts=20)
    except ValueError:
        return "excluded_missing_safe_generators"
    if not is_integer_answer(generated["answer"]):
        return "excluded_integer_answer"
    return None


def uses_source_values_fallback(template: dict[str, Any]) -> bool:
    answer_type = template.get("answer_type")
    if not isinstance(answer_type, str) or answer_type.strip().lower() != "unknown":
        return False
    if not _is_missing_formula(template):
        return False
    original_values = template.get("original_values", {})
    if not isinstance(original_values, dict):
        return False
    required = set(number_placeholder_names(str(template.get("template_text", ""))))
    return required == set(original_values)


def catalog_metadata() -> dict[str, Any]:
    result = filter_eligible_templates()
    return {
        "templates": [
            {
                "template_number": template.get("template_number"),
                "template_id": template.get("template_id"),
                "title": template.get("title"),
                "module_name": template.get("module_name"),
                "display_name": template.get("display_name"),
                "difficulty": template.get("difficulty"),
                "generation_mode": template.get("generation_mode"),
            }
            for template in result.eligible
        ],
        "stats": result.stats,
        "supported_answer_types": result.supported_answer_types,
    }


def template_by_id(template_id: str) -> dict[str, Any] | None:
    result = filter_eligible_templates()
    for template in result.eligible:
        if template.get("template_id") == template_id:
            return template
    return None


def render_template(template_text: str, values: dict[str, int | float | str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(f"Нет значения для {name}.")
        return str(values[name])

    rendered = NUMBER_PLACEHOLDER_RE.sub(replace, template_text)
    if ANY_PLACEHOLDER_RE.search(rendered):
        raise ValueError("В шаблоне остались незаполненные переменные.")
    return rendered


def literal_segments(template_text: str) -> list[str]:
    return NUMBER_PLACEHOLDER_RE.split(template_text)[::3]


def verify_literal_integrity(template_text: str, rendered: str) -> bool:
    position = 0
    for segment in literal_segments(template_text):
        found = rendered.find(segment, position)
        if found < position:
            return False
        position = found + len(segment)
    return True


def _candidate_values(template: dict[str, Any], rng: random.Random, require_changed: bool) -> dict[str, int]:
    original = template.get("original_values", {})
    if not isinstance(original, dict):
        original = {}
    names = number_placeholder_names(str(template.get("template_text", "")))
    values: dict[str, int] = {}
    changed = False
    for name in names:
        original_value = original.get(name, 1)
        if isinstance(original_value, int) and not isinstance(original_value, bool):
            low = 1 if original_value >= 0 else -30
            high = max(30, abs(original_value) * 2)
            value = rng.randint(low, high)
            if value != original_value:
                changed = True
        else:
            value = rng.randint(1, 30)
            changed = True
        values[name] = value
    if require_changed and names and not changed:
        first = names[0]
        values[first] = int(values[first]) + 1
    return values


def is_integer_answer(answer: Any) -> bool:
    if isinstance(answer, bool):
        return False
    if isinstance(answer, int):
        return True
    if isinstance(answer, float):
        return answer.is_integer()
    if isinstance(answer, (list, tuple, set)):
        return all(is_integer_answer(item) for item in answer)
    return False


def generate_problem_instance(
    template: dict[str, Any],
    rng: random.Random,
    *,
    require_changed: bool = True,
    max_attempts: int = MAX_ATTEMPTS,
) -> dict[str, Any]:
    source_template_text = template.get("template_text")
    if not isinstance(source_template_text, str):
        raise ValueError("У шаблона нет template_text.")
    if uses_source_values_fallback(template):
        original_values = template.get("original_values", {})
        rendered = render_template(source_template_text, original_values)
        if not verify_literal_integrity(source_template_text, rendered):
            raise ValueError(f"Не удалось сохранить текст шаблона №{template.get('template_number')}.")
        return {
            "template_number": template.get("template_number"),
            "template_id": template.get("template_id"),
            "title": template.get("title"),
            "generated_values": original_values,
            "rendered_problem": rendered,
            "answer": "Ответ не задан: в шаблоне нет answer_formula.",
            "attempts": 1,
            "generation_mode": "source_values_fallback",
        }
    for attempt in range(1, max_attempts + 1):
        values = _candidate_values(template, rng, require_changed=require_changed)
        candidate = copy.deepcopy(template)
        candidate["original_values"] = values
        try:
            answer = evaluate_formula(str(template["answer_formula"]), candidate)
        except Exception:
            continue
        if not type_matches(str(template["answer_type"]), answer):
            continue
        if not is_integer_answer(answer):
            continue
        rendered = render_template(source_template_text, values)
        if not verify_literal_integrity(source_template_text, rendered):
            continue
        return {
            "template_number": template.get("template_number"),
            "template_id": template.get("template_id"),
            "title": template.get("title"),
            "generated_values": values,
            "rendered_problem": rendered,
            "answer": int(answer) if isinstance(answer, float) and answer.is_integer() else answer,
            "attempts": attempt,
        }
    raise ValueError(f"Не удалось подобрать корректные целые значения для шаблона №{template.get('template_number')}.")


def generate_five_problem_worksheet(template_ids: list[str], seed: int | None = None) -> dict[str, Any]:
    if len(template_ids) != 5:
        raise ValueError("Выберите пять шаблонов.")
    if len(set(template_ids)) != 5:
        raise ValueError("Этот шаблон уже выбран. Повторение шаблонов выключено.")
    rng = random.Random(seed if seed is not None else datetime.now().timestamp())
    problems: list[dict[str, Any]] = []
    for position, template_id in enumerate(template_ids, start=1):
        template = template_by_id(template_id)
        if template is None:
            raise ValueError("Шаблон не поддерживает безопасную генерацию целых ответов.")
        generated = generate_problem_instance(template, rng)
        generated["position"] = position
        problems.append(generated)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": datetime.now().strftime("%d.%m.%Y"),
        "selected_templates": problems,
    }
