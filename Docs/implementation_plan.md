# Implementation Plan: full corpus tree and one-to-one templates

## Current structure

- Read-only corpus: `Docs/all_tasks_all_files.md`.
- Earlier tree references: `docs/math_problem_tree_100_themes.md`,
  `docs/math_problem_tree_full_coverage.md`,
  `data/source_index/math_problem_tree_template_ready.md`.
- Current incorrect bridge catalog: `data/templates/problem_templates.json`
  contains generated `tree_*` bridge records that do not provide one-to-one
  source-problem templates.
- Current template generator: `problemgen/generation/template_generator.py`.
- Current worksheet site: `problemgen/web/worksheet_site.py`,
  `frontend/worksheet_site.js`, `frontend/worksheet_site.css`.

## Target outputs

- `data/source_index/All_tasks_structure_tree.json`
- `data/source_index/All_tasks_rejected_problems.json`
- `data/templates/All_tasks_templates.json`
- `data/source_index/All_tasks_modules_summary.md`
- `data/templates/All_tasks_template_coverage_report.md`

Compatibility copies with the exact requested filenames may also be written in
the project root.

## Safe implementation steps

1. Read `Docs/all_tasks_all_files.md` without modifying it.
2. Extract numbered records and keep source PDF section names.
3. Clean obvious OCR artifacts deterministically without changing math meaning.
4. Classify each valid problem into exactly one primary mathematical module.
5. Reject only records that are empty, non-math, or unrecoverably damaged.
6. Write `All_tasks_structure_tree.json`.
7. Generate one numbered template per valid problem.
8. Parameterize numbers and repeated names/objects with stable placeholders.
9. Store `original_values` for reconstruction.
10. Validate uniqueness, template coverage, placeholder definitions, and
    reconstruction from original values.
11. Write summary and coverage reports.
12. Stop; no open-ended reclassification loop.

## Scope notes

- The first implementation is deterministic and conservative.
- Templates that cannot be safely randomized are marked
  `generation_status: requires_specialized_validator`.
- Original-value reconstruction is mandatory and must pass for every generated
  template.


# Cleanup Plan: number-only `all_tasks_templates.json`

## Current catalog inspection

- Source catalog: `data/templates/All_tasks_templates.json`.
- Current count: 2121 template records.
- Current placeholder families:
  - `number_*`: numerical placeholders;
  - `Entity_number_*`: incorrect non-number placeholders.
- Current issue: the prompt requires variables only for numbers, so every
  non-number placeholder and its metadata must be removed.

## Target files

- `data/templates/all_tasks_templates.json`
- `data/templates/all_tasks_templates_rejected.json`
- `data/templates/all_tasks_templates_cleanup_report.md`

Compatibility copies may also be written in the project root.

## Cleanup steps

1. Read the existing template catalog; do not rebuild the module tree.
2. For each template, start from `source_text`, not from old `template_text`.
3. Remove control/invisible characters and safe OCR artifacts.
4. Reject only records that remain unrecoverably damaged after safe cleaning.
5. Replace only numerical values with `{number_N}` placeholders in first-appearance order.
6. Keep names, locations, objects, nouns, verbs and units as literal Russian text.
7. Rebuild `placeholders`, `constraints`, and `original_values` with numerical
   placeholders only.
8. Preserve stable identity fields such as `template_number`, `template_id`,
   `source_problem_id`, `source_problem_number`, `module_id`, and difficulty.
9. Validate placeholder format, metadata consistency, forbidden characters, and
   reconstruction from `original_values`.
10. Write cleanup report and stop.
