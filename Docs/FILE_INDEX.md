# Индекс файлов

## Корень проекта

### `01.py`

Назначение:

- старый простой автономный генератор задач.

Когда открывать:

- если нужна ранняя минимальная версия без новой архитектуры.


### `02.py`

Назначение:

- основной launcher проекта.

Что внутри:

- импорт `problemgen.cli.main`;
- точка входа для `CLI` и локального сервера.

Когда открывать:

- если нужен самый верхний запуск проекта.


### `.gitignore`

Назначение:

- исключает из репозитория кэш Python и сгенерированные `JSON`-артефакты.

Когда открывать:

- если нужно изменить состав файлов, которые попадают в git.


### `DOCUMENTATION.md`

Назначение:

- полная техническая документация по новой архитектуре.


### `AGENTS.md`

Назначение:

- обязательные правила для следующих агентов.


## Пакет `problemgen/`

### `problemgen/app.py`

Назначение:

- центральный оркестратор генерации.

Ключевые сущности:

- `build_domain_catalog()`
- `get_domain(...)`
- `generate_problem_bundle(...)`

Связи:

- использует `problemgen/domains/*`;
- использует `problemgen/russian/validator.py`.


### `problemgen/cli.py`

Назначение:

- `CLI`-интерфейс проекта.

Ключевые сущности:

- `parse_args()`
- `run_cli(...)`
- `main()`

Связи:

- вызывает `problemgen/app.py`;
- вызывает `problemgen/web/server.py`.


## Папка `problemgen/core/`

### `problemgen/core/models.py`

Назначение:

- общие модели данных генератора.

Ключевые сущности:

- `TemplateDescriptor`
- `ProblemRecord`
- `GenerationBundle`


### `problemgen/core/difficulty.py`

Назначение:

- общие уровни сложности.

Ключевые сущности:

- `DifficultyLevel`
- `DIFFICULTY_LEVELS`


### `problemgen/core/themes.py`

Назначение:

- единый каталог тем и персонажей для новых доменов.

Ключевые сущности:

- `ThemeConfig`
- `THEMES`
- `sample_theme(...)`


## Папка `problemgen/russian/`

### `problemgen/russian/lexicon.py`

Назначение:

- единая структура словоформ.

Ключевые сущности:

- `NounForms`


### `problemgen/russian/agreement.py`

Назначение:

- согласование слов по числам и нормализация коротких фраз.

Ключевые сущности:

- `pluralize_ru(...)`
- `count_with_word_ru(...)`
- `normalize_sentence(...)`


### `problemgen/russian/validator.py`

Назначение:

- единая проверка русского языка для всех задач.

Ключевые сущности:

- `LanguageIssue`
- `validate_problem_record(...)`
- `attach_language_report(...)`


## Папка `problemgen/domains/`

### `problemgen/domains/base.py`

Назначение:

- абстрактный интерфейс домена задач.

Ключевые сущности:

- `MathDomain`


## Папка `problemgen/domains/segments/`

### `problemgen/domains/segments/domain.py`

Назначение:

- адаптер сегментного домена к новой архитектуре.

Ключевые сущности:

- `SegmentsDomain`
- `SEGMENT_TEMPLATE_LABELS`

Связи:

- использует `legacy_engine.py`;
- отдает сегментные задачи в общий формат `problemgen/app.py`.


### `problemgen/domains/segments/legacy_engine.py`

Назначение:

- прежний большой сегментный движок, сохраненный как совместимый модуль.

Что внутри:

- сюжеты;
- единицы измерения;
- сложности;
- шаблоны отрезков;
- старый сервер и старый `CLI`-слой legacy-версии.

Когда открывать:

- если нужно менять именно старые сегментные шаблоны;
- если нужно чинить темы или размерности для задач на отрезки.


## Папка `problemgen/domains/counting/`

### `problemgen/domains/counting/templates.py`

Назначение:

- шаблоны блока задач на счет.

Ключевые сущности:

- `COUNTING_RANGES`
- `generate_total_groups(...)`
- `generate_missing_group(...)`


### `problemgen/domains/counting/domain.py`

Назначение:

- доменный генератор задач на счет.

Ключевые сущности:

- `CountingDomain`


## Папка `problemgen/domains/combinatorics/`

### `problemgen/domains/combinatorics/templates.py`

Назначение:

- шаблоны блока задач на комбинаторику.

Ключевые сущности:

- `COMBINATORICS_RANGES`
- `generate_outfit_pairs(...)`
- `generate_route_pairs(...)`


### `problemgen/domains/combinatorics/domain.py`

Назначение:

- доменный генератор задач на комбинаторику.

Ключевые сущности:

- `CombinatoricsDomain`


## Папка `problemgen/web/`

### `problemgen/web/server.py`

Назначение:

- локальный HTTP-сервер и HTML-слой.

Ключевые сущности:

- `ProblemWebHandler`
- `render_page(...)`
- `render_problem_cards(...)`
- `create_http_server(...)`
- `run_server(...)`


## Папка `frontend/`

### `frontend/styles.css`

Назначение:

- стили локального сайта.

Особенности:

- светлая визуальная тема;
- LaTeX-like serif typography;
- карточки задач и адаптивная сетка.


### `frontend/app.js`

Назначение:

- интерактивное обновление выпадающих списков в форме сайта.

Ключевые сущности:

- `syncDomainOptions()`
- `refillSelect(...)`


## Папка `Docs/`

### `Docs/README.md`

Назначение:

- короткое описание папки документации.


### `Docs/FILE_INDEX.md`

Назначение:

- индекс файлов проекта.


### `Docs/VECTOR_TREE.md`

Назначение:

- смысловая навигация по новой архитектуре.


### `Docs/WORK_LOG.md`

Назначение:

- журнал изменений.


## Папка `output/`

Назначение:

- сгенерированные `JSON`-артефакты.

Важно:

- это не исходный код;
- логика генерации там не хранится.
