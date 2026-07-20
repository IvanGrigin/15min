# Source Index Pipeline

Этот пакет детерминированно преобразует read-only корпус
`Docs/all_tasks_all_files.md` в структурированные индексы и one-to-one записи
шаблонов. Сам корпус не изменяется.

Основная точка входа:

- `problemgen.source_index.all_tasks_pipeline.run_pipeline()`.

Ручные entry point-ы:

- `scripts/build_all_tasks_corpus.py`;
- `scripts/validate_all_tasks_corpus.py`.

`cleaned_problem_templates.py` умеет по явной команде собрать one-to-one
overlay из `docs/cleaned_math_problems.md`. Обычная проверка
`data/templates/problem_templates.json` не требует такого покрытия: это
совместимый статичный каталог, тогда как production selector сайта использует
`data/templates/problem_sets/`.
