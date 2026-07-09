"""I/O blueprint.

Do not remove this docstring without replacing it with a stricter contract.
This package should read project data and write generated bundles.
"""

from .worksheet_renderer import (
    ProblemSource,
    WorksheetRenderError,
    build_worksheet_plan,
    load_problem_source,
    load_problem_texts,
    load_worksheet_template,
    render_worksheet,
)

__all__ = [
    "ProblemSource",
    "WorksheetRenderError",
    "build_worksheet_plan",
    "load_problem_source",
    "load_problem_texts",
    "load_worksheet_template",
    "render_worksheet",
]
