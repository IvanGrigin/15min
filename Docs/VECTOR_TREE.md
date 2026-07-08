# Vector Tree

Это короткая смысловая навигация по текущей реализации и целевой архитектуре.

## Если нужен полный blueprint проекта

Смотреть:

- `Docs/ARCHITECTURE_BLUEPRINT.md`
- `Docs/REPOSITORY_STRUCTURE.md`
- `Docs/DATA_FLOW.md`


## Если нужно понять путь данных от исходных задач до итогового JSON

Смотреть:

- `Docs/DATA_FLOW.md`
- `data/source_index/`
- `data/templates/`
- `problemgen/generation/`
- `problemgen/language/`


## Если нужен верхний запуск текущей архитектуры

Смотреть:

- `scripts/run_problemgen.py`
- `problemgen/cli.py`
- `problemgen/app.py`

Что искать:

- `main()`
- `parse_args()`
- `run_cli(...)`
- `generate_problem_bundle(...)`


## Если нужен автономный простой генератор

Смотреть:

- `scripts/legacy_simple_generator.py`

Что искать:

- `ProblemTemplate`
- `build_*`
- `generate_*`


## Если нужен генератор задач про класс, дружбу и парты

Смотреть:

- `scripts/generate_friendship_class.py`

Что искать:

- `build_problem(...)`
- `plural(...)`
- `main()`

Результат:

- `outputs/friendship_class/1000_zadach.json`


## Если нужен общий оркестратор генерации

Смотреть:

- `problemgen/app.py`

Что искать:

- `build_domain_catalog()`
- `get_domain(...)`
- `generate_problem_bundle(...)`


## Если нужны общие миры, персонажи и локации

Смотреть:

- `problemgen/core/story_worlds.py`
- `Docs/STORY_WORLDS.md`

Что искать:

- `StoryWorld`
- `StoryContext`
- `STORY_WORLDS`
- `sample_story_context(...)`


## Если нужно работать с новым каталогом шаблонов

Смотреть:

- `data/templates/`
- `problemgen/catalog/README.md`


## Если нужно индексировать `all_tasks_all_files.md`

Смотреть:

- `Docs/all_tasks_all_files.md`
- `data/source_index/README.md`
- `data/source_index/tasks_index.example.json`
- `data/source_index/source_groups.example.json`

Важно:

- исходный файл не менять;
- разметку вести отдельно.


## Если нужны персонажи, локации и предметы

Смотреть:

- `data/entities/`
- `data/entities/roles.example.json`
- `problemgen/entities/README.md`


## Если нужны падежи, глагольные формы и управление

Смотреть:

- `data/language/`
- `problemgen/language/morphology/README.md`
- `problemgen/language/syntax/README.md`
- `problemgen/language/renderer/README.md`
- `problemgen/language/validators/README.md`


## Если нужно понять текущий совместимый русский слой

Смотреть:

- `problemgen/russian/README.md`
- `problemgen/russian/lexicon.py`
- `problemgen/russian/agreement.py`
- `problemgen/russian/validator.py`


## Если нужно понимать текущие рабочие домены

Смотреть:

- `problemgen/domains/counting/`
- `problemgen/domains/combinatorics/`
- `problemgen/domains/olympiad_logic/`
- `problemgen/domains/segments/`


## Если нужно добавлять новый математический блок

Смотреть:

- `problemgen/domains/README.md`
- `problemgen/domains/base.py`
- `problemgen/catalog/README.md`
- `data/templates/`


## Если нужны новые олимпиадные текстовые задачи

Смотреть:

- `problemgen/domains/olympiad_logic/domain.py`
- `problemgen/domains/olympiad_logic/templates.py`
- `problemgen/domains/olympiad_logic/solvers.py`
- `problemgen/domains/olympiad_logic/validators.py`

Что искать:

- `digit_erasing`
- `birds_count`
- `three_numbers_same_suffix`
- `shared_payment_debt`


## Если нужны задачи на отрезки

Смотреть:

- `problemgen/domains/segments/domain.py`
- `problemgen/domains/segments/legacy_engine.py`


## Если нужно менять уровни сложности

Смотреть:

- `problemgen/core/difficulty.py`
- для доменных диапазонов: `templates.py` нужного домена
- для legacy-отрезков: `problemgen/domains/segments/legacy_engine.py`


## Если нужно менять формат задачи и JSON-контракты

Смотреть:

- `data/schemas/task_template.example.json`
- `data/schemas/task_instance.example.json`
- `data/schemas/entity.example.json`
- `problemgen/core/models.py`
- `problemgen/core/README.md`


## Если нужен веб-интерфейс

Смотреть:

- `problemgen/web/server.py`
- `problemgen/web/README.md`
- `frontend/README.md`
- `frontend/styles.css`
- `frontend/app.js`


## Если нужно понять, где должны лежать результаты генерации

Смотреть:

- `outputs/README.md`
- `outputs/generated/README.md`


## Если нужно понять, что менялось недавно

Смотреть:

- `Docs/WORK_LOG.md`
