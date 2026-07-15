# All Tasks Answer Definition Cleanup Report

Recovery status: recovered.

- Templates recovered: 2119
- Retained template count: 2119
- Rejected template count: 2
- Missing answer definitions intentionally restored: 2119

## Note

The previous answer-definition filtering removed every template because all retained
records had `answer_type = "unknown"` and an empty `answer_formula`.

That filtering has been reversed. The catalog is restored to the number-only
template state, while the two older rejected non-problem fragments remain in
`all_tasks_templates_rejected.json`.

## Validation Commands

```powershell
python scripts/validate_clean_all_tasks_templates.py
```
