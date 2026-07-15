from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.source_index.all_tasks_pipeline import (
    REJECTED_PATH,
    TEMPLATES_PATH,
    TREE_PATH,
    validate_outputs,
)


def main() -> None:
    tree = json.loads(TREE_PATH.read_text(encoding="utf-8"))
    templates = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))["templates"]
    rejected = json.loads(REJECTED_PATH.read_text(encoding="utf-8"))["rejected_problems"]
    stats = validate_outputs(tree, templates, rejected)
    failures = (
        stats["duplicates"]
        + stats["missing_templates"]
        + len(stats["reconstruction_failures"])
        + len(stats["placeholder_failures"])
    )
    for key in (
        "extracted_records",
        "valid_problems",
        "rejected_records",
        "modules",
        "templates",
        "problems_covered_by_templates",
        "duplicates",
        "missing_templates",
        "reconstruction_tests_passed",
        "templates_requiring_specialized_validators",
    ):
        print(f"{key}: {stats[key]}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
