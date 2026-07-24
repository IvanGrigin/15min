"""Проверяет рендер активных модулей на запрещённые дефектные конструкции."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from problemgen.web.worksheet_site import VERIFIED_MODULE_IDS, generate_combined_worksheet_by_modules


FORBIDDEN = (
    "персонажу по имени",
    "ему или ей",
    "он/она",
    "его/её",
    "решил(а)",
    "получил/получила",
    "старший старше младшего",
    "В счёт первой доли",
    "Первые спешат",
)
PLACEHOLDER = re.compile(r"\{[^{}]+\}")
SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+[,.!?;:]")
ASCII_OR_CYRILLIC_MULTIPLICATION = re.compile(r"\d\s+[xх]\s+\d")


def validate_text(text: str) -> list[str]:
    issues = [f"запрещённая конструкция: {phrase}" for phrase in FORBIDDEN if phrase in text]
    if PLACEHOLDER.search(text):
        issues.append("неразрешённый placeholder")
    if "  " in text:
        issues.append("двойной пробел")
    if SPACE_BEFORE_PUNCTUATION.search(text):
        issues.append("пробел перед знаком препинания")
    if ASCII_OR_CYRILLIC_MULTIPLICATION.search(text):
        issues.append("не типографский знак умножения")
    return issues


def main() -> None:
    checked = 0
    for module_id in VERIFIED_MODULE_IDS:
        for seed in range(100):
            worksheet = generate_combined_worksheet_by_modules([module_id], seed=seed, task_count=1)
            problem = worksheet["selected_templates"][0]
            issues = validate_text(problem["rendered_problem"])
            if issues:
                raise AssertionError(
                    f"module={module_id} template={problem['template_id']} seed={seed}: {'; '.join(issues)}"
                )
            checked += 1
    print(f"OK: {checked} rendered active problems ({len(VERIFIED_MODULE_IDS)} modules × 100 seeds)")


if __name__ == "__main__":
    main()
