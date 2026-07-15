# All Tasks Templates Cleanup Report

- Original template count: 2121
- Retained template count: 2119
- Rejected template count: 2
- Templates repaired: 0
- Control characters removed: 0
- OCR fragments removed: 0
- Non-number placeholders removed: 0
- Templates containing only {number_N} placeholders: 2119
- Forbidden placeholders remaining: 0
- Control characters remaining: 0
- Templates failing reconstruction: 0
- Templates requiring manual review: 0

## Removed schema fields

- Non-number placeholder definitions such as `Entity_number_*`.
- Non-number entries in `constraints` and `original_values`.
- Any legacy metadata tied to name/entity replacement when present.

## Rejected templates

- #1114 `arithmetic_word_model_01114`: not_a_math_problem — The record is a grading/comment fragment rather than a recoverable math problem.
- #1130 `arithmetic_word_model_01130`: not_a_math_problem — The record is a grading/comment fragment rather than a recoverable math problem.

## Manual-review templates

- None.

## Representative before/after examples

## Validation commands

```powershell
python scripts/cleanup_all_tasks_templates.py
python scripts/validate_clean_all_tasks_templates.py
python -m unittest tests.test_all_tasks_template_cleanup
python -m unittest discover -s tests
```
