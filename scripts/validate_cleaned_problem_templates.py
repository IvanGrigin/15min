from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.source_index.cleaned_problem_templates import validate_current_catalog


def main() -> None:
    stats = validate_current_catalog()
    print(f"source_count: {stats['source_count']}")
    print(f"template_count: {stats['template_count']}")
    print(f"module_count: {stats['module_count']}")
    print("modules:")
    for module in stats["modules"]:
        print(f"- {module}")
    print(f"errors: {len(stats['errors'])}")
    for error in stats["errors"][:50]:
        print(f"- {error}")
    if stats["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
