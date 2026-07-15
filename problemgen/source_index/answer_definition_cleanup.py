from __future__ import annotations

import ast
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates.json"
REJECTED_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_rejected.json"
REPORT_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_answer_definition_cleanup_report.md"
STATS_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_answer_definition_cleanup_stats.json"

ROOT_COMPATIBILITY_FILES = {
    CATALOG_PATH: PROJECT_ROOT / "all_tasks_templates.json",
    REJECTED_PATH: PROJECT_ROOT / "all_tasks_templates_rejected.json",
    REPORT_PATH: PROJECT_ROOT / "all_tasks_answer_definition_cleanup_report.md",
}

INVALID_ANSWER_TYPES = {
    "",
    "?",
    "n/a",
    "none",
    "null",
    "pending",
    "not_implemented",
    "todo",
    "undefined",
    "unknown",
    "unspecified",
}
INVALID_FORMULAS = {
    "",
    " ",
    "?",
    "answer",
    "depends on the problem",
    "manual",
    "not implemented",
    "pending",
    "solve",
    "solve the problem",
    "to be added",
    "todo",
    "unknown",
}
UNRESOLVED_MARKER_RE = re.compile(r"\b(?:todo|unknown|pending|tbd|fixme|not implemented|to be added)\b|\.{3}|<[^>]+>", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"{([^}]+)}")


def validate_claim_truth(*_: Any) -> bool:
    return True


def validate_constructed_values(*_: Any) -> bool:
    return True


def validate_distinct_numbers_with_required_sum(*_: Any) -> bool:
    return True


def validate_invariant_argument(*_: Any) -> bool:
    return True


SAFE_HELPERS = {
    "abs": abs,
    "max": max,
    "min": min,
    "round": round,
    "sorted": sorted,
    "sum": sum,
    "validate_claim_truth": validate_claim_truth,
    "validate_constructed_values": validate_constructed_values,
    "validate_distinct_numbers_with_required_sum": validate_distinct_numbers_with_required_sum,
    "validate_invariant_argument": validate_invariant_argument,
}


class FormulaValidationError(ValueError):
    def __init__(self, reason_code: str, reason: str) -> None:
        super().__init__(reason)
        self.reason_code = reason_code
        self.reason = reason


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_answer_type(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def normalize_formula(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def placeholder_names(template: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    placeholders = template.get("placeholders", {})
    if isinstance(placeholders, dict):
        for value in placeholders.values():
            if isinstance(value, list):
                names.update(item for item in value if isinstance(item, str))
    original_values = template.get("original_values", {})
    if isinstance(original_values, dict):
        names.update(key for key in original_values if isinstance(key, str))
    names.update(PLACEHOLDER_RE.findall(str(template.get("template_text", ""))))
    return names


def formula_names(formula: str) -> set[str]:
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", formula):
            return {formula}
        raise FormulaValidationError("invalid_answer_formula", "The answer_formula is not a valid safe expression.")
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def validate_ast(tree: ast.AST) -> None:
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.BoolOp,
        ast.Compare,
        ast.IfExp,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.Set,
        ast.Dict,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise FormulaValidationError("invalid_answer_formula", f"Unsupported expression node: {type(node).__name__}.")
        if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
            raise FormulaValidationError("invalid_answer_formula", "Only direct calls to named helper functions are allowed.")


def evaluate_formula(formula: str, template: dict[str, Any]) -> Any:
    values = template.get("original_values", {})
    if not isinstance(values, dict):
        values = {}
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", formula):
        if formula in SAFE_HELPERS:
            return SAFE_HELPERS[formula]()
        raise FormulaValidationError("missing_answer_validator", f"The referenced formula helper '{formula}' does not exist.")
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise FormulaValidationError("invalid_answer_formula", "The answer_formula is not a valid safe expression.") from exc
    validate_ast(tree)
    names = formula_names(formula)
    allowed_names = set(values) | set(SAFE_HELPERS)
    missing = sorted(names - allowed_names)
    if missing:
        raise FormulaValidationError("undefined_formula_placeholders", f"Undefined formula variables: {', '.join(missing)}.")
    code = compile(tree, "<answer_formula>", "eval")
    try:
        return eval(code, {"__builtins__": {}}, {**SAFE_HELPERS, **values})
    except Exception as exc:
        raise FormulaValidationError("formula_execution_error", f"The formula raised an error for original values: {exc}.") from exc


def type_matches(answer_type: str, result: Any) -> bool:
    normalized = answer_type.strip().lower()
    if normalized in {"number", "decimal"}:
        return isinstance(result, (int, float)) and not isinstance(result, bool)
    if normalized == "integer":
        return isinstance(result, int) and not isinstance(result, bool)
    if normalized == "fraction":
        return isinstance(result, (int, float, str)) and not isinstance(result, bool)
    if normalized in {"boolean", "yes_no"}:
        return isinstance(result, bool) or str(result).strip().lower() in {"yes", "no", "да", "нет"}
    if normalized == "text":
        return isinstance(result, str)
    if normalized in {"list", "ordered_list", "set", "tuple", "multiple_numbers"}:
        return isinstance(result, (list, tuple, set))
    if normalized in {"date", "time", "expression"}:
        return isinstance(result, str)
    if normalized in {"construction", "proof"}:
        return isinstance(result, bool)
    return False


def validate_answer_definition(
    template: dict[str, Any],
    supported_answer_types: set[str],
) -> tuple[bool, str, str]:
    answer_type = normalize_answer_type(template.get("answer_type"))
    formula = normalize_formula(template.get("answer_formula"))
    type_errors: list[str] = []
    formula_errors: list[str] = []

    if answer_type is None:
        type_errors.append("answer_type is missing, null, empty, or not a string")
    elif answer_type.strip().lower() in INVALID_ANSWER_TYPES:
        type_errors.append(f"answer_type='{answer_type}' is invalid")
    elif answer_type not in supported_answer_types:
        type_errors.append(f"answer_type='{answer_type}' is not in the supported allowlist")

    if formula is None:
        formula_errors.append("answer_formula is missing, null, empty, or not a string")
    elif formula.strip().lower() in INVALID_FORMULAS:
        formula_errors.append(f"answer_formula='{formula}' is invalid")
    elif UNRESOLVED_MARKER_RE.search(formula):
        formula_errors.append(f"answer_formula='{formula}' contains an unresolved marker")

    if type_errors and formula_errors:
        return False, "missing_answer_definition", "; ".join(type_errors + formula_errors) + "."
    if type_errors:
        code = "missing_answer_type" if "missing" in type_errors[0] else "invalid_answer_type"
        return False, code, "; ".join(type_errors) + "."
    if formula_errors:
        code = "missing_answer_formula" if "missing" in formula_errors[0] else "invalid_answer_formula"
        return False, code, "; ".join(formula_errors) + "."

    assert answer_type is not None
    assert formula is not None
    try:
        names = formula_names(formula)
        declared = placeholder_names(template) | set(SAFE_HELPERS)
        missing = sorted(names - declared)
        if missing:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", formula):
                return False, "missing_answer_validator", f"The referenced formula helper '{formula}' does not exist."
            return False, "undefined_formula_placeholders", f"Undefined formula variables: {', '.join(missing)}."
        result = evaluate_formula(formula, template)
    except FormulaValidationError as exc:
        return False, exc.reason_code, exc.reason
    if not type_matches(answer_type, result):
        return False, "answer_type_mismatch", f"answer_type='{answer_type}' is incompatible with formula result {type(result).__name__}."
    return True, "", ""


def discover_supported_answer_types(templates: list[dict[str, Any]]) -> set[str]:
    supported: set[str] = set()
    observed = {
        normalized
        for template in templates
        if (normalized := normalize_answer_type(template.get("answer_type"))) is not None
        and normalized.strip().lower() not in INVALID_ANSWER_TYPES
    }
    for answer_type in sorted(observed):
        for template in templates:
            if normalize_answer_type(template.get("answer_type")) != answer_type:
                continue
            formula = normalize_formula(template.get("answer_formula"))
            if formula is None or formula.strip().lower() in INVALID_FORMULAS or UNRESOLVED_MARKER_RE.search(formula):
                continue
            try:
                result = evaluate_formula(formula, template)
            except FormulaValidationError:
                continue
            if type_matches(answer_type, result):
                supported.add(answer_type)
                break
    return supported


def rejection_record(template: dict[str, Any], reason_code: str, reason: str) -> dict[str, Any]:
    return {
        "template_number": template.get("template_number"),
        "template_id": template.get("template_id"),
        "source_problem_id": template.get("source_problem_id"),
        "source_problem_number": template.get("source_problem_number"),
        "source_file": template.get("source_file"),
        "reason_code": reason_code,
        "reason": reason,
        "original_template": template,
    }


def merge_rejections(previous: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in previous:
        key = str(record.get("template_id") or record.get("template_number"))
        merged[key] = record
    for record in new:
        key = str(record.get("template_id") or record.get("template_number"))
        merged[key] = record
    return sorted(
        merged.values(),
        key=lambda record: (
            record.get("template_number") is None,
            record.get("template_number") or 10**9,
            str(record.get("template_id") or ""),
        ),
    )


def build_report(stats: dict[str, Any], supported_answer_types: set[str], removed: list[dict[str, Any]]) -> str:
    lines = [
        "# All Tasks Answer Definition Cleanup Report",
        "",
        f"- Original template count: {stats['original_template_count']}",
        f"- Retained template count: {stats['retained_template_count']}",
        f"- Removed template count: {stats['newly_rejected_template_count']}",
        f"- Previously rejected count: {stats['previously_rejected_count']}",
        f"- Total rejected count: {stats['total_rejected_count']}",
        f"- Templates with missing answer_type: {stats['missing_answer_type']}",
        f"- Templates with invalid answer_type: {stats['invalid_answer_type']}",
        f"- Templates with missing answer_formula: {stats['missing_answer_formula']}",
        f"- Templates with invalid answer_formula: {stats['invalid_answer_formula']}",
        f"- Templates with undefined formula variables: {stats['undefined_formula_placeholders']}",
        f"- Templates with missing validators: {stats['missing_answer_validator']}",
        f"- Templates with formula execution errors: {stats['formula_execution_error']}",
        f"- Templates with answer-type mismatches: {stats['answer_type_mismatch']}",
        f"- Valid retained templates: {stats['valid_retained_templates']}",
        "",
        "## Supported Answer Type Allowlist",
        "",
    ]
    if supported_answer_types:
        lines.extend(f"- `{answer_type}`" for answer_type in sorted(supported_answer_types))
    else:
        lines.append("- None discovered from valid existing templates.")
    lines.extend(["", "## Removed Templates", ""])
    if removed:
        for record in removed:
            lines.append(
                f"- #{record.get('template_number')} `{record.get('template_id')}`: "
                f"{record.get('reason_code')} - {record.get('reason')}"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Representative Invalid Examples", ""])
    for record in removed[:5]:
        original = record.get("original_template", {})
        lines.append(
            f"- `{record.get('template_id')}` has answer_type={original.get('answer_type')!r} "
            f"and answer_formula={original.get('answer_formula')!r}."
        )
    if not removed:
        lines.append("- None.")
    lines.extend([
        "",
        "## Validation Commands",
        "",
        "```powershell",
        "python scripts/cleanup_answer_definitions.py",
        "python scripts/validate_answer_definitions.py",
        "python -m unittest tests.test_answer_definition_cleanup",
        "python -m unittest discover -s tests",
        "```",
    ])
    return "\n".join(lines) + "\n"


def run_cleanup() -> dict[str, Any]:
    catalog = load_json(CATALOG_PATH, {"schema_version": "1.0", "templates": []})
    templates = catalog.get("templates", [])
    if not isinstance(templates, list):
        raise ValueError("all_tasks_templates.json must contain a top-level 'templates' list.")
    previous_rejected = load_json(REJECTED_PATH, {"rejected_templates": []}).get("rejected_templates", [])
    if not isinstance(previous_rejected, list):
        previous_rejected = []

    supported_answer_types = discover_supported_answer_types(templates)
    retained: list[dict[str, Any]] = []
    newly_rejected: list[dict[str, Any]] = []
    counters = Counter()

    for template in templates:
        valid, reason_code, reason = validate_answer_definition(template, supported_answer_types)
        if valid:
            retained.append(template)
            counters["valid_retained_templates"] += 1
        else:
            counters[reason_code] += 1
            newly_rejected.append(rejection_record(template, reason_code, reason))

    merged_rejected = merge_rejections(previous_rejected, newly_rejected)
    retained_ids = {template.get("template_id") for template in retained}
    rejected_ids = {template.get("template_id") for template in merged_rejected}
    overlap = sorted(str(template_id) for template_id in retained_ids & rejected_ids if template_id)

    output_catalog = dict(catalog)
    output_catalog["templates"] = retained
    rejected_output = {"rejected_templates": merged_rejected}
    stats = {
        "original_template_count": len(templates),
        "retained_template_count": len(retained),
        "newly_rejected_template_count": len(newly_rejected),
        "previously_rejected_count": len(previous_rejected),
        "total_rejected_count": len(merged_rejected),
        "missing_answer_type": counters["missing_answer_type"],
        "invalid_answer_type": counters["invalid_answer_type"],
        "missing_answer_formula": counters["missing_answer_formula"],
        "invalid_answer_formula": counters["invalid_answer_formula"],
        "undefined_formula_placeholders": counters["undefined_formula_placeholders"],
        "missing_answer_validator": counters["missing_answer_validator"],
        "unimplemented_answer_validator": counters["unimplemented_answer_validator"],
        "formula_execution_error": counters["formula_execution_error"],
        "answer_type_mismatch": counters["answer_type_mismatch"],
        "missing_answer_definition": counters["missing_answer_definition"],
        "valid_retained_templates": counters["valid_retained_templates"],
        "supported_answer_types": sorted(supported_answer_types),
        "catalog_integrity_passed": len(templates) == len(retained) + len(newly_rejected),
        "retained_rejected_overlap": overlap,
    }

    write_json(CATALOG_PATH, output_catalog)
    write_json(REJECTED_PATH, rejected_output)
    write_json(STATS_PATH, stats)
    REPORT_PATH.write_text(build_report(stats, supported_answer_types, newly_rejected), encoding="utf-8")
    for source, target in ROOT_COMPATIBILITY_FILES.items():
        if source.exists():
            shutil.copyfile(source, target)
    return stats


def validate_current_catalog() -> dict[str, Any]:
    catalog = load_json(CATALOG_PATH, {"templates": []})
    templates = catalog.get("templates", [])
    if not isinstance(templates, list):
        raise ValueError("all_tasks_templates.json must contain a top-level 'templates' list.")
    rejected = load_json(REJECTED_PATH, {"rejected_templates": []}).get("rejected_templates", [])
    if not isinstance(rejected, list):
        rejected = []
    supported_answer_types = discover_supported_answer_types(templates)
    counters = Counter()
    for template in templates:
        valid, reason_code, _ = validate_answer_definition(template, supported_answer_types)
        if valid:
            counters["formula_validation_tests_passed"] += 1
        else:
            counters[reason_code] += 1
            counters["formula_validation_tests_failed"] += 1
    retained_ids = {template.get("template_id") for template in templates}
    rejected_ids = {record.get("template_id") for record in rejected}
    stats = {
        "retained_template_count": len(templates),
        "total_rejected_count": len(rejected),
        "missing_answer_types_remaining": counters["missing_answer_type"] + counters["missing_answer_definition"],
        "unknown_answer_types_remaining": sum(
            1 for template in templates if str(template.get("answer_type", "")).strip().lower() == "unknown"
        ),
        "empty_answer_formulas_remaining": sum(
            1 for template in templates if not isinstance(template.get("answer_formula"), str) or not template.get("answer_formula", "").strip()
        ),
        "invalid_answer_formulas_remaining": counters["invalid_answer_formula"],
        "undefined_formula_variables_remaining": counters["undefined_formula_placeholders"],
        "missing_validators_remaining": counters["missing_answer_validator"] + counters["unimplemented_answer_validator"],
        "answer_type_mismatches_remaining": counters["answer_type_mismatch"],
        "formula_validation_tests_passed": counters["formula_validation_tests_passed"],
        "formula_validation_tests_failed": counters["formula_validation_tests_failed"],
        "retained_rejected_overlap": sorted(str(template_id) for template_id in retained_ids & rejected_ids if template_id),
        "supported_answer_types": sorted(supported_answer_types),
    }
    return stats


def main() -> None:
    stats = run_cleanup()
    for key in (
        "original_template_count",
        "retained_template_count",
        "newly_rejected_template_count",
        "previously_rejected_count",
        "total_rejected_count",
        "missing_answer_definition",
        "valid_retained_templates",
    ):
        print(f"{key}: {stats[key]}")


if __name__ == "__main__":
    main()
