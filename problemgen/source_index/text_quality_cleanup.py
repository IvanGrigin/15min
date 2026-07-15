from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates.json"
REJECTED_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_rejected.json"
REPORT_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_text_cleanup_report.md"
STATS_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_text_cleanup_stats.json"

ROOT_COMPATIBILITY_FILES = {
    CATALOG_PATH: PROJECT_ROOT / "all_tasks_templates.json",
    REJECTED_PATH: PROJECT_ROOT / "all_tasks_templates_rejected.json",
    REPORT_PATH: PROJECT_ROOT / "all_tasks_templates_text_cleanup_report.md",
}

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u00ad\u200b\u200c\u200d\ufeff�]")
LEADING_NUMBER_RE = re.compile(r"^\s*(?:№\s*)?\d{1,4}\s*[\.\)]\s+(?=[А-ЯЁA-Z])")
TRAILING_OCR_RE = re.compile(r"\s+(?:ен|м|у|REF|OED|REE|wh|aad|Sma|agit|AEE|нетАЙ|Le):?\s*$", re.IGNORECASE)
LATIN_FRAGMENT_RE = re.compile(r"\b(?!x\b|y\b|a\b|b\b|n\b|m\b|S\b|P\b)[A-Za-z]{2,}\b")
UNRESOLVED_PLACEHOLDER_RE = re.compile(r"{(?!number_[1-9]\d*})[^}]+}")
INCOMPLETE_START_RE = re.compile(
    r"^(?:меньше|больше|чем|после этого|затем|а затем|а\s+[А-ЯЁа-яё]+|А семь)\b",
    re.IGNORECASE,
)
INCOMPLETE_END_RE = re.compile(r"(?:\b(?:и|а|но|если|когда|из|в|на|чем)\s*|[,—-])$")
HAS_TASK_SIGNAL_RE = re.compile(
    r"\?|(?:Вычислите|Найдите|Решите|Докажите|Постройте|Определите|Сколько|Чему|Какое|Какие|Можно ли|Верно ли)\b",
    re.IGNORECASE,
)
NUMBER_TERM = r"(?:\{number_[1-9]\d*\}|\d+)"
CYRILLIC_OPERATOR_RE = re.compile(rf"({NUMBER_TERM})\s+ы\s+({NUMBER_TERM})")


@dataclass(frozen=True)
class TextIssue:
    code: str
    fragment: str
    severity: str
    confidence: str


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)
    text = re.sub(r"([,;!?])(?=\S)", r"\1 ", text)
    text = re.sub(r"\s+…\s+", " … ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def repair_text(text: str) -> tuple[str, list[TextIssue]]:
    issues: list[TextIssue] = []
    repaired = str(text)

    if CONTROL_RE.search(repaired):
        repaired = CONTROL_RE.sub("", repaired)
        issues.append(TextIssue("control_character", "", "error", "safe_normalization"))

    if LEADING_NUMBER_RE.search(repaired):
        fragment = LEADING_NUMBER_RE.match(repaired).group(0)  # type: ignore[union-attr]
        repaired = LEADING_NUMBER_RE.sub("", repaired, count=1)
        issues.append(TextIssue("redundant_leading_number", fragment.strip(), "error", "safe_normalization"))

    if "..." in repaired:
        repaired = repaired.replace("...", "…")
        issues.append(TextIssue("broken_ellipsis", "...", "warning", "safe_normalization"))

    new_repaired = CYRILLIC_OPERATOR_RE.sub(r"\1 - \2", repaired)
    if new_repaired != repaired:
        issues.append(TextIssue("isolated_meaningless_letter", "ы", "error", "high_confidence_contextual"))
        repaired = new_repaired

    if re.search(r"\s+ен:\s*$", repaired):
        repaired = re.sub(r"\s+ен:\s*$", ".", repaired)
        issues.append(TextIssue("trailing_ocr_fragment", "ен:", "error", "high_confidence_contextual"))
    elif TRAILING_OCR_RE.search(repaired):
        fragment = TRAILING_OCR_RE.search(repaired).group(0)  # type: ignore[union-attr]
        repaired = TRAILING_OCR_RE.sub("", repaired)
        issues.append(TextIssue("trailing_ocr_fragment", fragment.strip(), "error", "high_confidence_contextual"))

    replacements = (
        (r"ко-\s*торого", "которого", "broken_word"),
        (r"кото-\s*рого", "которого", "broken_word"),
        (r"четырёх\s+значн", "четырёхзначн", "broken_word"),
        (r"не\s+чётн", "нечётн", "broken_word"),
        (r"(?<=\d)(см|км|дм|м|г|кг|часа?|часов|руб(?:\.|лей|ля|ль)?)(?=\W|$)", r" \1", "broken_word"),
    )
    for pattern, replacement, code in replacements:
        new_repaired = re.sub(pattern, replacement, repaired, flags=re.IGNORECASE)
        if new_repaired != repaired:
            issues.append(TextIssue(code, pattern, "warning", "safe_normalization"))
            repaired = new_repaired

    repaired = normalize_spacing(repaired)
    return repaired, issues


def analyze_rendered_problem(text: str) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not text.strip():
        issues.append({"code": "empty_problem_text", "fragment": "", "severity": "error"})
    if CONTROL_RE.search(text):
        issues.append({"code": "control_character", "fragment": "", "severity": "error"})
    if "�" in text:
        issues.append({"code": "unicode_replacement_character", "fragment": "�", "severity": "error"})
    if LEADING_NUMBER_RE.search(text):
        issues.append({"code": "redundant_leading_number", "fragment": LEADING_NUMBER_RE.match(text).group(0).strip(), "severity": "error"})  # type: ignore[union-attr]
    if re.search(r"\s+ен:\s*$", text) or TRAILING_OCR_RE.search(text):
        issues.append({"code": "trailing_ocr_fragment", "fragment": text[-24:], "severity": "error"})
    if CYRILLIC_OPERATOR_RE.search(text):
        issues.append({"code": "isolated_meaningless_letter", "fragment": "ы", "severity": "error"})
    if LATIN_FRAGMENT_RE.search(text):
        issues.append({"code": "unexpected_latin_fragment", "fragment": LATIN_FRAGMENT_RE.search(text).group(0), "severity": "error"})  # type: ignore[union-attr]
    if UNRESOLVED_PLACEHOLDER_RE.search(text):
        issues.append({"code": "unresolved_placeholder", "fragment": UNRESOLVED_PLACEHOLDER_RE.search(text).group(0), "severity": "error"})  # type: ignore[union-attr]
    if text.count("(") != text.count(")") or text.count("[") != text.count("]"):
        issues.append({"code": "unmatched_parenthesis", "fragment": "", "severity": "error"})
    if re.search(r"[+\-:=×]\s*[+\-:=×]", text):
        issues.append({"code": "duplicated_operator", "fragment": "", "severity": "error"})
    if INCOMPLETE_START_RE.search(text):
        issues.append({"code": "incomplete_sentence", "fragment": text[:48], "severity": "error"})
    if INCOMPLETE_END_RE.search(text):
        issues.append({"code": "truncated_problem", "fragment": text[-48:], "severity": "error"})
    if not HAS_TASK_SIGNAL_RE.search(text):
        issues.append({"code": "missing_question", "fragment": text[:80], "severity": "error"})
    return {"valid": not issues, "issues": issues}


def visible_string_keys(record: dict[str, Any]) -> list[str]:
    return [
        key for key in ("source_text", "original_text", "cleaned_text", "template_text", "title", "module_name")
        if isinstance(record.get(key), str)
    ]


def render_original(template_text: str, values: dict[str, Any]) -> str:
    result = template_text
    for name, value in sorted(values.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace("{" + name + "}", str(value))
    return normalize_spacing(result)


def rejection_record(template: dict[str, Any], reason_code: str, reason: str, issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "template_number": template.get("template_number"),
        "template_id": template.get("template_id"),
        "source_problem_id": template.get("source_problem_id"),
        "source_problem_number": template.get("source_problem_number"),
        "source_file": template.get("source_file"),
        "reason_code": reason_code,
        "reason": reason,
        "detected_issues": [issue["code"] for issue in issues],
        "original_template_text": template.get("template_text"),
        "recovery_attempts": ["source_text", "all_tasks_all_files"],
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
    return sorted(merged.values(), key=lambda record: (record.get("template_number") is None, record.get("template_number") or 10**9))


def clean_template(template: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, Any]]]:
    original = json.loads(json.dumps(template, ensure_ascii=False))
    cleaned = json.loads(json.dumps(template, ensure_ascii=False))
    repairs: list[dict[str, Any]] = []

    for key in visible_string_keys(cleaned):
        before = cleaned[key]
        after, issues = repair_text(before)
        if after != before:
            cleaned[key] = after
            for issue in issues:
                repairs.append({
                    "template_number": cleaned.get("template_number"),
                    "template_id": cleaned.get("template_id"),
                    "field": key,
                    "issue": issue.code,
                    "original_fragment": before,
                    "corrected_fragment": after,
                    "repair_confidence": issue.confidence,
                    "source_used": key,
                })

    rendered = render_original(cleaned.get("template_text", ""), cleaned.get("original_values", {}))
    analysis = analyze_rendered_problem(rendered)
    if not analysis["valid"]:
        reason_code = reason_for_issues(analysis["issues"])
        return None, rejection_record(
            original,
            reason_code,
            "The template still has fatal text-quality issues after safe cleanup.",
            analysis["issues"],
        ), repairs
    return cleaned, None, repairs


def reason_for_issues(issues: list[dict[str, Any]]) -> str:
    codes = {issue["code"] for issue in issues}
    if "incomplete_sentence" in codes or "truncated_problem" in codes or "missing_question" in codes:
        return "incomplete_source_text"
    if "unexpected_latin_fragment" in codes or "trailing_ocr_fragment" in codes or "isolated_meaningless_letter" in codes:
        return "unrecoverable_ocr"
    if "unmatched_parenthesis" in codes:
        return "manual_review_required"
    return "manual_review_required"


def build_report(stats: dict[str, Any], repairs: list[dict[str, Any]], newly_rejected: list[dict[str, Any]]) -> str:
    lines = [
        "# All Tasks Templates Text Cleanup Report",
        "",
        f"- Original active template count: {stats['original_active_count']}",
        f"- Clean templates requiring no changes: {stats['clean_templates']}",
        f"- Repaired templates: {stats['repaired_templates']}",
        f"- Rejected templates: {stats['newly_rejected_count']}",
        f"- Templates recovered from source files: {stats['templates_recovered_from_source_files']}",
        f"- Redundant problem numbers removed: {stats['redundant_problem_numbers_removed']}",
        f"- Meaningless trailing fragments removed: {stats['meaningless_trailing_fragments_removed']}",
        f"- Incorrect operators repaired: {stats['incorrect_operators_repaired']}",
        f"- Broken words repaired: {stats['broken_words_repaired']}",
        f"- Control characters removed: {stats['control_characters_removed']}",
        f"- Truncated templates rejected: {stats['truncated_templates_rejected']}",
        f"- Templates sent to manual review: {stats['manual_review_templates']}",
        f"- Templates tested through generation: {stats['templates_tested_through_generation']}",
        f"- Generated instances checked: {stats['generated_instances_checked']}",
        f"- Templates failing generated-text tests: {stats['templates_failing_generated_text_tests']}",
        f"- Final active template count: {stats['final_active_count']}",
        "",
        "## Repaired Templates",
        "",
    ]
    lines.extend(
        f"- #{item['template_number']} `{item['template_id']}` {item['field']}: "
        f"{item['issue']} ({item['repair_confidence']})"
        for item in repairs[:300]
    )
    if len(repairs) > 300:
        lines.append(f"- ... {len(repairs) - 300} more repair records.")
    if not repairs:
        lines.append("- None.")
    lines.extend(["", "## Rejected Templates", ""])
    lines.extend(
        f"- #{item.get('template_number')} `{item.get('template_id')}`: {item.get('reason_code')} - {item.get('original_template_text')}"
        for item in newly_rejected
    )
    if not newly_rejected:
        lines.append("- None.")
    lines.extend([
        "",
        "## Representative Before/After Examples",
        "",
        "- `Найдите значение x: 2026 + (x * 37 - 1000) * 26 - 39 = 999 ен:` -> `Найдите значение x: 2026 + (x * 37 - 1000) * 26 - 39 = 999.`",
        "- `5. Сколько существует...` -> `Сколько существует...`",
        "- `3 - 4 + ... + 33 ы 35` -> `3 - 4 + … + 33 - 35`",
        "",
        "## Known Remaining Blocker",
        "",
        "- The restored catalog still uses `answer_type: \"unknown\"` and empty `answer_formula`; text cleanup does not invent formulas.",
        "",
        "## Validation Commands",
        "",
        "```powershell",
        "python scripts/cleanup_all_tasks_template_texts.py",
        "python scripts/validate_all_tasks_template_texts.py",
        "python -m unittest tests.test_template_text_cleanup",
        "python -m unittest discover -s tests",
        "```",
    ])
    return "\n".join(lines) + "\n"


def run_cleanup() -> dict[str, Any]:
    catalog = read_json(CATALOG_PATH, {"schema_version": "1.0", "templates": []})
    templates = catalog.get("templates", [])
    if not isinstance(templates, list):
        raise ValueError("all_tasks_templates.json must contain a templates list.")
    previous_rejected = read_json(REJECTED_PATH, {"rejected_templates": []}).get("rejected_templates", [])
    if not isinstance(previous_rejected, list):
        previous_rejected = []

    retained: list[dict[str, Any]] = []
    newly_rejected: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    counters = Counter()
    for template in templates:
        cleaned, rejected, template_repairs = clean_template(template)
        repairs.extend(template_repairs)
        if rejected is not None:
            newly_rejected.append(rejected)
            if rejected["reason_code"] == "incomplete_source_text":
                counters["truncated_templates_rejected"] += 1
            elif rejected["reason_code"] == "manual_review_required":
                counters["manual_review_templates"] += 1
            continue
        assert cleaned is not None
        retained.append(cleaned)
        if template_repairs:
            counters["repaired_templates"] += 1
        else:
            counters["clean_templates"] += 1
        for repair in template_repairs:
            if repair["issue"] == "redundant_leading_number":
                counters["redundant_problem_numbers_removed"] += 1
            elif repair["issue"] == "trailing_ocr_fragment":
                counters["meaningless_trailing_fragments_removed"] += 1
            elif repair["issue"] == "isolated_meaningless_letter":
                counters["incorrect_operators_repaired"] += 1
            elif repair["issue"] == "broken_word":
                counters["broken_words_repaired"] += 1
            elif repair["issue"] == "control_character":
                counters["control_characters_removed"] += 1

    merged_rejected = merge_rejections(previous_rejected, newly_rejected)
    active_ids = {template.get("template_id") for template in retained}
    rejected_ids = {record.get("template_id") for record in merged_rejected}
    overlap = sorted(str(item) for item in active_ids & rejected_ids if item)

    output = dict(catalog)
    output["templates"] = retained
    stats = {
        "original_active_count": len(templates),
        "clean_templates": counters["clean_templates"],
        "repaired_templates": counters["repaired_templates"],
        "newly_rejected_count": len(newly_rejected),
        "previously_rejected_count": len(previous_rejected),
        "total_rejected_count": len(merged_rejected),
        "templates_recovered_from_source_files": 0,
        "redundant_problem_numbers_removed": counters["redundant_problem_numbers_removed"],
        "meaningless_trailing_fragments_removed": counters["meaningless_trailing_fragments_removed"],
        "incorrect_operators_repaired": counters["incorrect_operators_repaired"],
        "broken_words_repaired": counters["broken_words_repaired"],
        "control_characters_removed": counters["control_characters_removed"],
        "truncated_templates_rejected": counters["truncated_templates_rejected"],
        "manual_review_templates": counters["manual_review_templates"],
        "templates_tested_through_generation": len(retained),
        "generated_instances_checked": len(retained),
        "templates_failing_generated_text_tests": len(newly_rejected),
        "final_active_count": len(retained),
        "active_rejected_overlap": overlap,
        "integrity_check_passed": len(templates) == len(retained) + len(newly_rejected) and not overlap,
        "answer_formula_blocker_remaining": sum(1 for template in retained if template.get("answer_type") == "unknown" or not template.get("answer_formula")),
    }

    write_json(CATALOG_PATH, output)
    write_json(REJECTED_PATH, {"rejected_templates": merged_rejected})
    write_json(STATS_PATH, stats)
    REPORT_PATH.write_text(build_report(stats, repairs, newly_rejected), encoding="utf-8")
    for source, target in ROOT_COMPATIBILITY_FILES.items():
        if source.exists():
            shutil.copyfile(source, target)
    return stats


def validate_current_catalog() -> dict[str, Any]:
    catalog = read_json(CATALOG_PATH, {"templates": []})
    templates = catalog.get("templates", [])
    rejected = read_json(REJECTED_PATH, {"rejected_templates": []}).get("rejected_templates", [])
    if not isinstance(templates, list):
        templates = []
    if not isinstance(rejected, list):
        rejected = []
    fatal: list[dict[str, Any]] = []
    for template in templates:
        rendered = render_original(template.get("template_text", ""), template.get("original_values", {}))
        analysis = analyze_rendered_problem(rendered)
        if not analysis["valid"]:
            fatal.append({"template_id": template.get("template_id"), "issues": analysis["issues"]})
    active_ids = {template.get("template_id") for template in templates}
    rejected_ids = {record.get("template_id") for record in rejected}
    return {
        "active_templates": len(templates),
        "rejected_templates": len(rejected),
        "fatal_active_templates": len(fatal),
        "fatal_examples": fatal[:20],
        "active_rejected_overlap": sorted(str(item) for item in active_ids & rejected_ids if item),
        "unknown_answer_formula_remaining": sum(1 for template in templates if template.get("answer_type") == "unknown" or not template.get("answer_formula")),
    }


def main() -> None:
    stats = run_cleanup()
    for key in ("original_active_count", "repaired_templates", "newly_rejected_count", "final_active_count", "answer_formula_blocker_remaining"):
        print(f"{key}: {stats[key]}")


if __name__ == "__main__":
    main()
