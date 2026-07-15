# Source Index Pipeline

This package contains deterministic code for converting the read-only corpus
`Docs/all_tasks_all_files.md` into structured source indexes and one-to-one
template records.

Main entry point:

- `problemgen.source_index.all_tasks_pipeline.run_pipeline()`

Manual scripts:

- `scripts/build_all_tasks_corpus.py`
- `scripts/validate_all_tasks_corpus.py`

The pipeline does not modify the source corpus. It writes canonical outputs to
`data/source_index/` and `data/templates/`, plus compatibility copies with the
requested filenames in the project root.
