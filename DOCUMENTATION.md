# Документация по проекту

## Что это за проект

Проект генерирует математические задачи и сохраняет результаты в текстовые или `JSON`-файлы.

Сейчас в проекте есть три основных типа запуска:

- `scripts/run_problemgen.py` — основной launcher модульной архитектуры;
- `scripts/legacy_simple_generator.py` — ранний автономный генератор;
- `scripts/generate_friendship_class.py` — отдельный генератор задач про класс, дружбу и парты.


## Главная идея структуры

Проект разделен по ролям файлов:

1. `problemgen/`
   - переиспользуемая логика;
   - домены задач;
   - общий `CLI`;
   - веб-слой;
   - русский язык и валидация.

2. `scripts/`
   - короткие entry point-файлы;
   - отдельные запускаемые сценарии;
   - место для новых генераторов, которые пользователь запускает вручную.

3. `outputs/`
   - все сгенерированные артефакты;
   - текстовые выгрузки;
   - примеры `JSON`.

4. `docs/`
   - индекс файлов;
   - смысловая навигация;
   - журнал изменений.

5. `tests/`
   - будущие автоматические проверки генераторов.


## Точка входа новой архитектуры

### `scripts/run_problemgen.py`

Сейчас это тонкий launcher.

Его задача:

- добавить корень проекта в `sys.path`;
- импортировать `problemgen.cli.main`;
- запускать `CLI` или локальный сервер.


## Автономные скрипты

### `scripts/legacy_simple_generator.py`

Что делает:

- генерирует задачи старого standalone-формата;
- хранит шаблоны и диапазоны прямо в одном файле;
- может сохранять результат в `JSON`.


### `scripts/generate_friendship_class.py`

Что делает:

- создает 1000 текстовых задач про класс, дружбу и парты;
- меняет имена и числа;
- следит, чтобы ответ и внутренние величины были целыми;
- сохраняет результат в `outputs/friendship_class/1000_zadach.txt`.


## Пакет `problemgen/`

### `problemgen/cli.py`

Главный интерфейс запуска.

Что делает:

- разбирает аргументы командной строки;
- выбирает домен задач;
- запускает генерацию;
- печатает задачи в консоль;
- запускает локальный сервер по флагу `--serve`.

Основные флаги:

- `--serve`
- `--host`
- `--port`
- `--domain`
- `--count`
- `--template-name`
- `--difficulty-level`
- `--story-theme`
- `--seed-mode`
- `--seed`
- `--mode`
- `--output`


### `problemgen/app.py`

Оркестратор всего приложения.

Что делает:

- собирает каталог доменов;
- вызывает нужный домен;
- нормализует формат задач;
- прогоняет общую проверку русского языка;
- пересохраняет итоговый `JSON` после общей валидации.


## Общие слои

### `problemgen/core/models.py`

Главные структуры данных:

- `TemplateDescriptor`
- `ProblemRecord`
- `GenerationBundle`


### `problemgen/core/difficulty.py`

Общие уровни сложности:

- `easy`
- `medium`
- `hard`


### `problemgen/core/themes.py`

Единый каталог сюжетных тем.

Что содержит:

- `ThemeConfig`
- `THEMES`
- `get_theme(...)`
- `sample_theme(...)`


## Русский язык

### `problemgen/russian/lexicon.py`

Содержит `NounForms` — центральную структуру для словоформ.


### `problemgen/russian/agreement.py`

Содержит:

- `pluralize_ru(...)`
- `count_with_word_ru(...)`
- `join_with_comma_and(...)`
- `normalize_sentence(...)`


### `problemgen/russian/validator.py`

Содержит:

- `LanguageIssue`
- `validate_problem_record(...)`
- `attach_language_report(...)`


## Домены задач

### `problemgen/domains/segments/`

Блок задач на отрезки.

Главные файлы:

- `domain.py` — адаптер домена к общей архитектуре;
- `legacy_engine.py` — старый большой движок, сохраненный как совместимый модуль.


### `problemgen/domains/counting/`

Блок задач на счет.

Главные файлы:

- `templates.py`
- `domain.py`


### `problemgen/domains/combinatorics/`

Блок задач на комбинаторику.

Главные файлы:

- `templates.py`
- `domain.py`


## Веб-слой

### `problemgen/web/server.py`

Что делает:

- поднимает локальный сервер;
- рендерит HTML;
- раздает `frontend/styles.css` и `frontend/app.js`;
- выдает `JSON` на скачивание;
- показывает задачи, ответы и замечания языковой проверки.


## Фронтенд

### `frontend/styles.css`

Отвечает за внешний вид сайта.


### `frontend/app.js`

Отвечает за интерактивность формы.


## Где лежат результаты

- `outputs/samples/` — сохраненные примеры `JSON`;
- `outputs/friendship_class/` — текстовые наборы задач про класс;
- будущие массовые генерации тоже должны сохраняться в `outputs/`, а не в корень проекта.


## Типичные запуски

### Консоль, новая архитектура

```bash
python3 scripts/run_problemgen.py --domain counting --count 5 --difficulty-level easy --story-theme space
```

### Консоль, комбинаторика

```bash
python3 scripts/run_problemgen.py --domain combinatorics --count 5 --difficulty-level hard --story-theme cowboy
```

### Локальный сайт

```bash
python3 scripts/run_problemgen.py --serve
```

### Генератор дружбы в классе

```bash
python3 scripts/generate_friendship_class.py
```


## Что открывать в зависимости от задачи

- если нужен новый запускаемый сценарий: `scripts/`
- если нужно менять общий запуск: `scripts/run_problemgen.py`, `problemgen/cli.py`
- если нужно менять маршрутизацию доменов: `problemgen/app.py`
- если нужно чинить русский язык во всех новых задачах сразу: `problemgen/russian/`
- если нужно добавлять новый блок математики: `problemgen/domains/`
- если нужно менять UI: `problemgen/web/server.py`, `frontend/styles.css`, `frontend/app.js`
- если нужно проверить структуру проекта: `AGENTS.md`, `docs/FILE_INDEX.md`, `docs/VECTOR_TREE.md`
