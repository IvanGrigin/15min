from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.source_index.answer_definition_cleanup import validate_current_catalog


def main() -> None:
    stats = validate_current_catalog()
    for key in (
        "retained_template_count",
        "total_rejected_count",
        "missing_answer_types_remaining",
        "unknown_answer_types_remaining",
        "empty_answer_formulas_remaining",
        "invalid_answer_formulas_remaining",
        "undefined_formula_variables_remaining",
        "missing_validators_remaining",
        "answer_type_mismatches_remaining",
        "formula_validation_tests_passed",
        "formula_validation_tests_failed",
    ):
        print(f"{key}: {stats[key]}")
    failures = (
        stats["missing_answer_types_remaining"]
        + stats["unknown_answer_types_remaining"]
        + stats["empty_answer_formulas_remaining"]
        + stats["invalid_answer_formulas_remaining"]
        + stats["undefined_formula_variables_remaining"]
        + stats["missing_validators_remaining"]
        + stats["answer_type_mismatches_remaining"]
        + stats["formula_validation_tests_failed"]
        + len(stats["retained_rejected_overlap"])
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
