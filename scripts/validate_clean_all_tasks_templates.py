from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.source_index.template_cleanup import (
    CLEAN_TEMPLATE_PATH,
    REJECTED_TEMPLATE_PATH,
    validate_clean_catalog,
)


def main() -> None:
    templates = json.loads(CLEAN_TEMPLATE_PATH.read_text(encoding="utf-8"))["templates"]
    rejected = json.loads(REJECTED_TEMPLATE_PATH.read_text(encoding="utf-8"))["rejected_templates"]
    stats_path = PROJECT_ROOT / "data" / "templates" / "all_tasks_templates_cleanup_stats.json"
    original = json.loads(stats_path.read_text(encoding="utf-8"))["original_template_records"]
    stats = validate_clean_catalog(templates, rejected, original)
    for key in (
        "original_template_records",
        "retained_template_records",
        "rejected_template_records",
        "templates_with_only_number_placeholders",
        "forbidden_placeholders_remaining",
        "control_characters_remaining",
        "reconstruction_tests_passed",
        "reconstruction_tests_failed",
    ):
        print(f"{key}: {stats[key]}")
    failures = (
        stats["forbidden_placeholders_remaining"]
        + stats["control_characters_remaining"]
        + stats["reconstruction_tests_failed"]
        + len(stats["metadata_failures"])
    )
    if not stats["coverage_check_passed"] or failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
