from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.worksheet.all_tasks_site import catalog_metadata


def main() -> None:
    metadata = catalog_metadata()
    print(json.dumps({
        "stats": metadata["stats"],
        "supported_answer_types": metadata["supported_answer_types"],
        "selectable_templates_passing_all_tests": len(metadata["templates"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
