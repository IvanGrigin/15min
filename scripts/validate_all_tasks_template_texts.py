from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.source_index.text_quality_cleanup import validate_current_catalog


def main() -> None:
    stats = validate_current_catalog()
    for key in (
        "active_templates",
        "rejected_templates",
        "fatal_active_templates",
        "unknown_answer_formula_remaining",
    ):
        print(f"{key}: {stats[key]}")
    if stats["fatal_active_templates"] or stats["active_rejected_overlap"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
