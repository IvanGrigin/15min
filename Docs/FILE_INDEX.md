# Индекс файлов

## Корень проекта

### `README.md`

Назначение:

- краткое описание проекта и текущей структуры.


### `.gitignore`

Назначение:

- исключает кэш Python и массовые выходные артефакты.


### `AGENTS.md`

Назначение:

- обязательные правила для следующих агентов;
- фиксирует целевую структуру проекта.


### `DOCUMENTATION.md`

Назначение:

- полная техническая документация по текущей архитектуре.


## Папка `scripts/`

### `scripts/run_problemgen.py`

Назначение:

- основной entry point модульной архитектуры.

Ключевые сущности:

- `main()`

Связи:

- импортирует `problemgen.cli`.


### `scripts/legacy_simple_generator.py`

Назначение:

- ранний автономный генератор задач;
- полезен как простая standalone-версия без веб-слоя и доменной архитектуры.

Ключевые сущности:

- `NumberRange`
- `ProblemTemplate`
- `build_*`-шаблоны


### `scripts/generate_friendship_class.py`

Назначение:

- генерирует 1000 текстовых задач про класс, дружбу и парты;
- сохраняет итог в `outputs/friendship_class/1000_zadach.txt`.

Ключевые сущности:

- `plural(...)`
- `build_problem(...)`
- `main()`


### `scripts/README.md`

Назначение:

- объясняет правила для запускаемых вручную скриптов.


## Папка `problemgen/`

### `problemgen/app.py`

Назначение:

- центральный оркестратор генерации.

Ключевые сущности:

- `build_domain_catalog()`
- `get_domain(...)`
- `generate_problem_bundle(...)`


### `problemgen/cli.py`

Назначение:

- `CLI`-интерфейс проекта.

Ключевые сущности:

- `parse_args()`
- `run_cli(...)`
- `main()`


## Папка `problemgen/core/`

### `problemgen/core/models.py`

Назначение:

- общие модели данных генератора.


### `problemgen/core/difficulty.py`

Назначение:

- общие уровни сложности.


### `problemgen/core/themes.py`

Назначение:

- единый каталог тем и персонажей для новых доменов.


## Папка `problemgen/russian/`

### `problemgen/russian/lexicon.py`

Назначение:

- единая структура словоформ.


### `problemgen/russian/agreement.py`

Назначение:

- согласование слов по числам и нормализация коротких фраз.


### `problemgen/russian/validator.py`

Назначение:

- единая проверка русского языка для всех задач.


## Папка `problemgen/domains/`

### `problemgen/domains/base.py`

Назначение:

- абстрактный интерфейс домена задач.


### `problemgen/domains/segments/domain.py`

Назначение:

- адаптер сегментного домена к новой архитектуре.


### `problemgen/domains/segments/legacy_engine.py`

Назначение:

- прежний большой сегментный движок, сохраненный как совместимый модуль.


### `problemgen/domains/counting/templates.py`

Назначение:

- шаблоны блока задач на счет.


### `problemgen/domains/counting/domain.py`

Назначение:

- доменный генератор задач на счет.


### `problemgen/domains/combinatorics/templates.py`

Назначение:

- шаблоны блока задач на комбинаторику.


### `problemgen/domains/combinatorics/domain.py`

Назначение:

- доменный генератор задач на комбинаторику.


## Папка `problemgen/web/`

### `problemgen/web/server.py`

Назначение:

- локальный HTTP-сервер и HTML-слой.


## Папка `frontend/`

### `frontend/styles.css`

Назначение:

- стили локального сайта.


### `frontend/app.js`

Назначение:

- интерактивное обновление формы сайта.


## Папка `outputs/`

### `outputs/README.md`

Назначение:

- объясняет, какие артефакты хранятся в `outputs/`.


### `outputs/samples/generated_problems.json`

Назначение:

- пример JSON-выгрузки раннего генератора.


### `outputs/samples/sample_output.json`

Назначение:

- пример итоговой JSON-выгрузки модульного генератора.


### `outputs/samples/sample_segments.json`

Назначение:

- пример выгрузки сегментных задач.


### `outputs/friendship_class/1000_zadach.txt`

Назначение:

- пример текстовой выгрузки набора задач про класс и дружбу.


## Папка `tests/`

### `tests/README.md`

Назначение:

- фиксирует ожидаемые направления для автоматических проверок.


## Папка `docs/`

### `docs/README.md`

Назначение:

- короткое описание папки документации.


### `docs/FILE_INDEX.md`

Назначение:

- индекс файлов проекта.


### `docs/VECTOR_TREE.md`

Назначение:

- смысловая навигация по архитектуре.


### `docs/WORK_LOG.md`

Назначение:

- журнал изменений.
