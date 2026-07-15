from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "All_tasks_templates.json"
CLEAN_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates.json"
REJECTED_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_rejected.json"
CLEANUP_REPORT_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_cleanup_report.md"
VALIDATION_STATS_PATH = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_cleanup_stats.json"

ROOT_COMPATIBILITY_FILES = {
    CLEAN_TEMPLATE_PATH: PROJECT_ROOT / "all_tasks_templates.json",
    REJECTED_TEMPLATE_PATH: PROJECT_ROOT / "all_tasks_templates_rejected.json",
    CLEANUP_REPORT_PATH: PROJECT_ROOT / "all_tasks_templates_cleanup_report.md",
}

FORBIDDEN_PLACEHOLDER_RE = re.compile(r"{(?!number_[1-9]\d*})[^}]+}")
NUMBER_RE = re.compile(r"\d+(?::\d+){1,2}|\d+(?:[.,]\d+)?")
PLACEHOLDER_RE = re.compile(r"{(number_[1-9]\d*)}")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u00ad\u200b\u200c\u200d\ufeff�]")
ESCAPED_CONTROL_RE = re.compile(r"\\u00(?:0[0-8bcef]|1[0-9a-f]|7f)", re.IGNORECASE)
SUSPICIOUS_RE = re.compile(
    r"ко-\s*торого|кото-\s*рого|ПОСТУПЛЕНИЕ|одно число верно|без сантиметров|"
    r"\b(?:aad|Sma|REF|OED|S22|agit|AEE|нетАЙ|Le|wh)\b|\[=\]|\[al\]",
    re.IGNORECASE,
)
INVALID_GRADING_FRAGMENT_RE = re.compile(
    r"только одно число верное|перепутаны имена|не снимать|числа верные\s+\d+\s*б",
    re.IGNORECASE,
)
REJECT_RE = re.compile(r"�|\\u00(?:0[0-8bcef]|1[0-9a-f]|7f)", re.IGNORECASE)


def normalize_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)
    text = re.sub(r"([,;!?])(?=\S)", r"\1 ", text)
    text = re.sub(r"(?<=\d)\s*:\s*(?=\d{2}\b)", ":", text)
    text = re.sub(r"(?<=\D)\s*:\s*(?=\D)", ": ", text)
    text = re.sub(r"\s*([+\-=])\s*", r" \1 ", text)
    text = re.sub(r"\s*×\s*", " × ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_visible_text(text: str) -> tuple[str, dict[str, int]]:
    stats = Counter()
    before = text
    text = CONTROL_RE.sub("", text)
    if text != before:
        stats["control_characters_removed"] += 1
    if ESCAPED_CONTROL_RE.search(text):
        text = ESCAPED_CONTROL_RE.sub("", text)
        stats["control_escape_sequences_removed"] += 1

    replacements = (
        (r"ко-\s*торого", "которого"),
        (r"кото-\s*рого", "которого"),
        (r"(\d)\s*см2\b", r"\1 см²"),
        (r"(\d)\s*см3\b", r"\1 см³"),
        (r"(\d)(см|км|дм|м|г|кг|часа?|часов|руб(?:\.|лей|ля|ль)?)(?=\W|$)", r"\1 \2"),
        (r"(?<=\d)\s*[xх*]\s*(?=\d)", " × "),
        (r"\bПОСТУПЛЕНИЕ\b", " "),
        (r"\[=\]|\[al\]", " "),
        (r"\b(?:aad|Sma|REF|OED|S22|agit|AEE|нетАЙ|Le|wh)\b", " "),
        (r"\bодно число верно, второе нет\b", " "),
        (r"\bбез сантиметров\b", " "),
        (r"\s+[.‚,]*\s*239[.`]?\s*$", ""),
        (r"\s+[.‚,]*\s*[A-Za-z]{2,}\s*$", ""),
    )
    for pattern, replacement in replacements:
        new_text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if new_text != text:
            stats["ocr_fragments_removed"] += 1
        text = new_text

    text = normalize_spacing(text)
    return text, dict(stats)


def original_number_value(raw: str) -> int | float | str:
    if ":" in raw:
        return raw
    if len(raw) > 1 and raw.startswith("0"):
        return raw
    normalized = raw.replace(",", ".")
    if "." in normalized:
        try:
            return float(normalized)
        except ValueError:
            return raw
    try:
        return int(raw)
    except ValueError:
        return raw


def number_constraint(raw: str, before: str, after: str) -> dict[str, Any]:
    constraint: dict[str, Any] = {
        "type": "time" if ":" in raw else ("number" if "," in raw or "." in raw else "integer"),
        "original": original_number_value(raw),
        "min": 0,
    }
    next_words = re.findall(r"^[\s.,;:!?-]*([А-Яа-яЁёA-Za-z²³]+)", after)
    if next_words:
        constraint["fixed_following_word"] = next_words[0]
        constraint["agreement_note"] = "Generated values must match the fixed Russian word form in template_text."
    prev_words = re.findall(r"([А-Яа-яЁёA-Za-z]+)[\s.,;:!?-]*$", before)
    if prev_words:
        constraint["previous_word"] = prev_words[-1]
    return constraint


def parameterize_numbers_only(text: str) -> tuple[str, dict[str, list[str]], dict[str, Any], dict[str, Any]]:
    placeholders: list[str] = []
    original_values: dict[str, Any] = {}
    constraints: dict[str, Any] = {}
    parts: list[str] = []
    last = 0
    counter = 1
    for match in NUMBER_RE.finditer(text):
        raw = match.group(0)
        name = f"number_{counter}"
        placeholders.append(name)
        original_values[name] = original_number_value(raw)
        constraints[name] = number_constraint(raw, text[max(0, match.start() - 32):match.start()], text[match.end():match.end() + 32])
        parts.append(text[last:match.start()])
        parts.append("{" + name + "}")
        last = match.end()
        counter += 1
    parts.append(text[last:])
    return "".join(parts), {"numbers": placeholders}, constraints, original_values


def reconstruct(template_text: str, original_values: dict[str, Any]) -> str:
    result = template_text
    for name, value in sorted(original_values.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace("{" + name + "}", str(value))
    return result


def comparable(text: str) -> str:
    return normalize_spacing(text)


def should_reject(cleaned_text: str) -> tuple[bool, str, str]:
    if len(cleaned_text) < 8:
        return True, "invalid_source_record", "The cleaned text is too short to be a recoverable math problem."
    if REJECT_RE.search(cleaned_text) or CONTROL_RE.search(cleaned_text):
        return True, "unrecoverable_ocr", "The text still contains forbidden replacement or control characters after cleanup."
    if INVALID_GRADING_FRAGMENT_RE.search(cleaned_text):
        return True, "not_a_math_problem", "The record is a grading/comment fragment rather than a recoverable math problem."
    return False, "", ""


def clean_template_record(template: dict[str, Any], catalog_position: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, int]]:
    stats = Counter()
    source_text = template.get("source_text") or template.get("cleaned_text") or template.get("template_text", "")
    cleaned_text, clean_stats = clean_visible_text(str(source_text))
    stats.update(clean_stats)
    reject, reason_code, reason = should_reject(cleaned_text)
    if reject:
        return None, {
            "template_number": template.get("template_number"),
            "template_id": template.get("template_id"),
            "source_problem_id": template.get("source_problem_id"),
            "source_problem_number": template.get("source_problem_number"),
            "original_text": source_text,
            "reason_code": reason_code,
            "reason": reason,
        }, dict(stats)

    template_text, placeholders, constraints, original_values = parameterize_numbers_only(cleaned_text)
    if FORBIDDEN_PLACEHOLDER_RE.search(template_text):
        return None, {
            "template_number": template.get("template_number"),
            "template_id": template.get("template_id"),
            "source_problem_id": template.get("source_problem_id"),
            "source_problem_number": template.get("source_problem_number"),
            "original_text": source_text,
            "reason_code": "invalid_source_record",
            "reason": "Template text still contains a forbidden non-number placeholder after cleanup.",
        }, dict(stats)

    retained = {
        key: template[key]
        for key in (
            "template_number", "template_id", "source_problem_id", "source_problem_number",
            "source_file", "module_id", "module_name", "difficulty", "title", "answer_type",
            "answer_formula", "validation_rules", "generation_status",
        )
        if key in template
    }
    retained.update({
        "catalog_position": catalog_position,
        "source_text": cleaned_text,
        "template_text": template_text,
        "placeholders": placeholders,
        "constraints": constraints,
        "original_values": original_values,
        "literal_number_exceptions": [],
    })
    stats["non_number_placeholders_removed"] += len(re.findall(r"{(?!number_[1-9]\d*})[^}]+}", template.get("template_text", "")))
    if cleaned_text != source_text or template_text != template.get("template_text"):
        stats["templates_repaired"] += 1
    return retained, None, dict(stats)


def validate_clean_catalog(templates: list[dict[str, Any]], rejected: list[dict[str, Any]], original_count: int) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "original_template_records": original_count,
        "retained_template_records": len(templates),
        "rejected_template_records": len(rejected),
        "templates_with_only_number_placeholders": 0,
        "forbidden_placeholders_remaining": 0,
        "control_characters_remaining": 0,
        "reconstruction_tests_passed": 0,
        "reconstruction_tests_failed": 0,
        "metadata_failures": [],
        "manual_review_records": [],
    }
    for template in templates:
        text = template["template_text"]
        used = PLACEHOLDER_RE.findall(text)
        all_placeholders = re.findall(r"{([^}]+)}", text)
        expected = [f"number_{index}" for index in range(1, len(used) + 1)]
        numbers = template["placeholders"].get("numbers", [])
        if all(name.startswith("number_") for name in all_placeholders):
            stats["templates_with_only_number_placeholders"] += 1
        if len(all_placeholders) != len(used):
            stats["forbidden_placeholders_remaining"] += 1
        if CONTROL_RE.search(json.dumps(template, ensure_ascii=False)) or ESCAPED_CONTROL_RE.search(json.dumps(template, ensure_ascii=False)):
            stats["control_characters_remaining"] += 1
        if used != expected or numbers != expected:
            stats["metadata_failures"].append(template["template_number"])
        if set(template["original_values"]) != set(expected) or set(template["constraints"]) != set(expected):
            stats["metadata_failures"].append(template["template_number"])
        rebuilt = reconstruct(text, template["original_values"])
        if comparable(rebuilt) == comparable(template["source_text"]) and "{" not in rebuilt:
            stats["reconstruction_tests_passed"] += 1
        else:
            stats["reconstruction_tests_failed"] += 1
            stats["manual_review_records"].append(template["template_number"])
        if SUSPICIOUS_RE.search(template["source_text"]):
            stats["manual_review_records"].append(template["template_number"])
    stats["manual_review_records"] = sorted(set(stats["manual_review_records"]))
    stats["coverage_check_passed"] = original_count == len(templates) + len(rejected)
    return stats


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(stats: dict[str, Any], aggregate: Counter, rejected: list[dict[str, Any]], before_after: list[tuple[str, str]]) -> None:
    lines = [
        "# All Tasks Templates Cleanup Report",
        "",
        f"- Original template count: {stats['original_template_records']}",
        f"- Retained template count: {stats['retained_template_records']}",
        f"- Rejected template count: {stats['rejected_template_records']}",
        f"- Templates repaired: {aggregate['templates_repaired']}",
        f"- Control characters removed: {aggregate['control_characters_removed'] + aggregate['control_escape_sequences_removed']}",
        f"- OCR fragments removed: {aggregate['ocr_fragments_removed']}",
        f"- Non-number placeholders removed: {aggregate['non_number_placeholders_removed']}",
        f"- Templates containing only {{number_N}} placeholders: {stats['templates_with_only_number_placeholders']}",
        f"- Forbidden placeholders remaining: {stats['forbidden_placeholders_remaining']}",
        f"- Control characters remaining: {stats['control_characters_remaining']}",
        f"- Templates failing reconstruction: {stats['reconstruction_tests_failed']}",
        f"- Templates requiring manual review: {len(stats['manual_review_records'])}",
        "",
        "## Removed schema fields",
        "",
        "- Non-number placeholder definitions such as `Entity_number_*`.",
        "- Non-number entries in `constraints` and `original_values`.",
        "- Any legacy metadata tied to name/entity replacement when present.",
        "",
        "## Rejected templates",
        "",
    ]
    if rejected:
        for item in rejected:
            lines.append(f"- #{item['template_number']} `{item['template_id']}`: {item['reason_code']} — {item['reason']}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Manual-review templates", ""])
    if stats["manual_review_records"]:
        for number in stats["manual_review_records"][:200]:
            lines.append(f"- Template {number}")
        if len(stats["manual_review_records"]) > 200:
            lines.append(f"- ...and {len(stats['manual_review_records']) - 200} more.")
    else:
        lines.append("- None.")
    lines.extend(["", "## Representative before/after examples", ""])
    for before, after in before_after[:5]:
        lines.extend(["Before:", "", f"> {before}", "", "After:", "", f"> {after}", ""])
    lines.extend([
        "## Validation commands",
        "",
        "```powershell",
        "python scripts/cleanup_all_tasks_templates.py",
        "python scripts/validate_clean_all_tasks_templates.py",
        "python -m unittest tests.test_all_tasks_template_cleanup",
        "python -m unittest discover -s tests",
        "```",
        "",
    ])
    CLEANUP_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def copy_compatibility_outputs() -> None:
    for source, target in ROOT_COMPATIBILITY_FILES.items():
        shutil.copyfile(source, target)


def run_cleanup() -> dict[str, Any]:
    payload = json.loads(SOURCE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    source_templates = payload["templates"]
    retained: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    aggregate = Counter()
    before_after: list[tuple[str, str]] = []

    for template in source_templates:
        clean_record, rejected_record, stats = clean_template_record(template, len(retained) + 1)
        aggregate.update(stats)
        if rejected_record is not None:
            rejected.append(rejected_record)
            continue
        assert clean_record is not None
        if clean_record["template_text"] != template.get("template_text"):
            before_after.append((template.get("template_text", ""), clean_record["template_text"]))
        retained.append(clean_record)

    output = {
        "schema_version": payload.get("schema_version", "1.0"),
        "source_catalog": str(SOURCE_TEMPLATE_PATH.relative_to(PROJECT_ROOT)),
        "templates": retained,
    }
    rejected_output = {"rejected_templates": rejected}
    stats = validate_clean_catalog(retained, rejected, len(source_templates))
    stats.update({
        "templates_repaired": aggregate["templates_repaired"],
        "control_characters_removed": aggregate["control_characters_removed"] + aggregate["control_escape_sequences_removed"],
        "ocr_fragments_removed": aggregate["ocr_fragments_removed"],
        "non_number_placeholders_removed": aggregate["non_number_placeholders_removed"],
    })

    write_json(CLEAN_TEMPLATE_PATH, output)
    write_json(REJECTED_TEMPLATE_PATH, rejected_output)
    write_json(VALIDATION_STATS_PATH, stats)
    write_report(stats, aggregate, rejected, before_after)
    copy_compatibility_outputs()
    return stats


def main() -> None:
    stats = run_cleanup()
    for key in (
        "original_template_records",
        "retained_template_records",
        "rejected_template_records",
        "templates_repaired",
        "templates_with_only_number_placeholders",
        "forbidden_placeholders_remaining",
        "control_characters_remaining",
        "reconstruction_tests_passed",
        "reconstruction_tests_failed",
    ):
        print(f"{key}: {stats[key]}")


if __name__ == "__main__":
    main()
