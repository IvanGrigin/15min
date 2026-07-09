# Документация по проекту

## Что это за проект

Проект генерирует математические задачи и сохраняет результаты в текстовые или `JSON`-файлы.

## Важное обновление по архитектуре

Помимо описания текущей рабочей реализации, в репозитории теперь есть отдельные документы с целевой архитектурой:

- `Docs/ARCHITECTURE_BLUEPRINT.md` — целевой blueprint;
- `Docs/REPOSITORY_STRUCTURE.md` — роли папок и файлов;
- `Docs/DATA_FLOW.md` — путь данных от исходных задач к итоговому JSON.

Если задача касается роста проекта, слоев русского языка, словарей сущностей, масштабирования шаблонов или новых уровней абстракции, сначала нужно читать именно эти документы, а уже потом смотреть текущую реализацию.

Сейчас в проекте есть три основных типа запуска:

- `scripts/run_problemgen.py` — основной launcher модульной архитектуры;
- `scripts/legacy_simple_generator.py` — ранний автономный генератор;
- `scripts/generate_friendship_class.py` — отдельный генератор задач про класс, дружбу и парты.

Сейчас в модульной архитектуре есть домены:

- `segments`
- `counting`
- `combinatorics`
- `olympiad_logic`
- `arithmetic` — классические текстовые задачи с правильной русской морфологией


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

- создает 1000 задач про класс, дружбу и парты;
- берет персонажей, локации и миры из общего слоя `problemgen/core/story_worlds.py`;
- следит, чтобы ответ и внутренние величины были целыми;
- сохраняет результат в `outputs/friendship_class/1000_zadach.json`.


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
- `--story-world`
- `--list-story-worlds`
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


### `problemgen/core/story_worlds.py`

Единый каталог сюжетных миров, персонажей и локаций.

Что содержит:

- `StoryWorld`
- `StoryContext`
- `STORY_WORLDS`
- `get_story_world(...)`
- `list_story_worlds()`
- `sample_story_world(...)`
- `sample_story_context(...)`


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


### `problemgen/domains/olympiad_logic/`

Блок олимпиадных логических задач.

Главные файлы:

- `domain.py` — доменный генератор;
- `templates.py` — шаблоны задач;
- `solvers.py` — вычисление ответов;
- `validators.py` — проверки корректности параметров и ответов.


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
- `outputs/friendship_class/` — JSON-наборы задач про класс;
- `outputs/generated/` — стандартные JSON-выгрузки модульных доменов;
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

### Олимпиадная логика

```bash
python3 scripts/run_problemgen.py --domain olympiad_logic --count 5 --story-world smeshariki
```

### Олимпиадная логика, конкретный шаблон

```bash
python3 scripts/run_problemgen.py --domain olympiad_logic --template-name digit_erasing --count 3 --story-world prostokvashino
```

### Локальный сайт

```bash
python3 scripts/run_problemgen.py --serve
```

### Генератор дружбы в классе

```bash
python3 scripts/generate_friendship_class.py
```

### Список сюжетных миров

```bash
python3 scripts/run_problemgen.py --list-story-worlds
```


## Что открывать в зависимости от задачи

- если нужен новый запускаемый сценарий: `scripts/`
- если нужно менять общий запуск: `scripts/run_problemgen.py`, `problemgen/cli.py`
- если нужно менять маршрутизацию доменов: `problemgen/app.py`
- если нужно добавлять или менять миры, персонажей и локации: `problemgen/core/story_worlds.py`, `docs/STORY_WORLDS.md`
- если нужно чинить русский язык во всех новых задачах сразу: `problemgen/russian/`
- если нужно добавлять новый блок математики: `problemgen/domains/`
- если нужны олимпиадные текстовые шаблоны: `problemgen/domains/olympiad_logic/`
- если нужны классические арифметические задачи с правильным склонением: `problemgen/domains/arithmetic/`, документация: `Docs/RUSSIAN_TEMPLATES.md`
- если нужно добавить новое существительное в словарь: `data/language/nouns/russian_nouns.json` (инструкция в `data/language/nouns/README.md`)
- если нужна документация по системе морфологических шаблонов: `Docs/RUSSIAN_TEMPLATES.md`
- если нужно менять UI: `problemgen/web/server.py`, `frontend/styles.css`, `frontend/app.js`
- если нужно проверить структуру проекта: `AGENTS.md`, `docs/FILE_INDEX.md`, `docs/VECTOR_TREE.md`
