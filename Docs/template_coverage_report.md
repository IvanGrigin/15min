# Template Coverage Status

## Current, verifiable state

- Numbered records in the immutable corpus: **2,121**.
- Navigation leaves in [`data/source_index/task_tree/`](../data/source_index/task_tree/README.md): **100**.
- Runtime JSON templates in `data/templates/problem_templates.json`: **9**.
- Runtime templates with a one-to-one `source_bindings` record: **0**.

The tree is an index for finding and formalizing families of tasks. It does **not** establish runtime generator coverage. A future coverage report may claim exact one-to-one coverage only after the corresponding catalog artifacts, source bindings, and reproducible round-trip tests are committed.

## Navigation

- [Task-tree root](../data/source_index/task_tree/README.md) — branch index and usage notes.
- [Machine-readable manifest](../data/source_index/task_tree/manifest.json) — 100 paths and mapped-record totals.
- [Runtime template catalog](../data/templates/problem_templates.json) — templates that the active worksheet generator can actually load.
