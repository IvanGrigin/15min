from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from problemgen.core.models import ProblemRecord


@dataclass(frozen=True)
class LanguageIssue:
    level: str
    field: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _validate_text(text: str, field: str) -> List[LanguageIssue]:
    issues: List[LanguageIssue] = []

    if not text.strip():
        issues.append(LanguageIssue("error", field, "Пустой текст."))
        return issues

    if "  " in text:
        issues.append(LanguageIssue("warning", field, "Есть двойные пробелы."))

    if text[0].isalpha() and text[0] != text[0].upper():
        issues.append(LanguageIssue("warning", field, "Текст начинается не с заглавной буквы."))

    if field == "problem_text" and text[-1] not in ".?!":
        issues.append(LanguageIssue("warning", field, "Условие должно заканчиваться знаком препинания."))

    if ".." in text:
        issues.append(LanguageIssue("warning", field, "Есть повторяющиеся точки."))

    return issues


def validate_problem_record(problem: ProblemRecord) -> List[LanguageIssue]:
    issues = []
    issues.extend(_validate_text(problem.problem_text, "problem_text"))
    issues.extend(_validate_text(problem.answer_text, "answer_text"))

    if not problem.answer_values:
        issues.append(LanguageIssue("error", "answer_values", "Не заполнен числовой ответ."))

    unit_short = str(problem.story.get("unit_short", "")).strip()
    if unit_short and problem.category == "segments":
        text_blob = f"{problem.problem_text} {problem.answer_text}"
        if unit_short not in text_blob:
            issues.append(
                LanguageIssue(
                    "warning",
                    "unit_short",
                    "Единица измерения указана в сюжете, но не обнаружена в тексте задачи или ответа.",
                )
            )

    return issues


def attach_language_report(problem: ProblemRecord) -> ProblemRecord:
    issues = [issue.to_dict() for issue in validate_problem_record(problem)]
    problem.metadata["language_issues"] = issues
    problem.metadata["language_status"] = "ok" if not issues else "needs_review"
    return problem
