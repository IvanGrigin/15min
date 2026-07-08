# Индекс файлов

Этот индекс описывает ключевые файлы, текущие рабочие модули и новые архитектурные слои проекта.

## Корень проекта

### `README.md`

Назначение:

- краткое верхнеуровневое описание проекта;
- ссылка на целевой архитектурный blueprint;
- краткая карта текущих рабочих доменов.


### `.gitignore`

Назначение:

- исключает кэш Python и массовые выходные артефакты.


### `AGENTS.md`

Назначение:

- обязательные правила для будущих агентов;
- порядок чтения документации;
- запрет на удаление архитектурных комментариев и README без замены.


### `DOCUMENTATION.md`

Назначение:

- описание текущей рабочей реализации;
- ссылка на новые архитектурные документы.


## Папка `Docs/`

### `Docs/README.md`

Назначение:

- объясняет состав документации;
- фиксирует, что `all_tasks_all_files.md` остается read-only источником.


### `Docs/ARCHITECTURE_BLUEPRINT.md`

Назначение:

- описывает целевую архитектуру проекта;
- разделяет read-only корпус, данные, генерацию, язык и вывод.


### `Docs/REPOSITORY_STRUCTURE.md`

Назначение:

- объясняет, что должно лежать в каждой важной папке;
- фиксирует ответственность слоев и каталогов.


### `Docs/DATA_FLOW.md`

Назначение:

- описывает путь данных от `Docs/all_tasks_all_files.md` до готового JSON.


### `Docs/STORY_WORLDS.md`

Назначение:

- инструкция по использованию общего слоя сюжетных миров.


### `Docs/VECTOR_TREE.md`

Назначение:

- короткая смысловая навигация по репозиторию.


### `Docs/WORK_LOG.md`

Назначение:

- журнал работ и архитектурных изменений.


### `Docs/all_tasks_all_files.md`

Назначение:

- основной read-only корпус примеров и типов задач.

Правило:

- не редактировать.


## Папка `data/`

### `data/README.md`

Назначение:

- вводное описание слоя проектных данных;
- правило, что здесь нет исполняемой логики.


### `data/schemas/README.md`

Назначение:

- описывает схемы и примеры контрактов данных.


### `data/schemas/task_template.example.json`

Назначение:

- пример структуры формального шаблона задачи.


### `data/schemas/task_instance.example.json`

Назначение:

- пример структуры готового экземпляра задачи.


### `data/schemas/entity.example.json`

Назначение:

- пример структуры сущности с падежными формами.


### `data/schemas/verb_lexeme.example.json`

Назначение:

- пример структуры глагольной рамки и управления.


### `data/taxonomy/README.md`

Назначение:

- описание классификаторов задач.


### `data/taxonomy/categories.example.json`

Назначение:

- пример суперкатегорий и подкатегорий.


### `data/taxonomy/genres.example.json`

Назначение:

- пример жанров, отделенных от математики.


### `data/taxonomy/feature_flags.example.json`

Назначение:

- пример flags для фильтрации задач.


### `data/taxonomy/difficulty_scale.example.json`

Назначение:

- пример шкалы сложности 1–10.


### `data/source_index/README.md`

Назначение:

- описание слоя разметки исходного корпуса задач.


### `data/source_index/tasks_index.example.json`

Назначение:

- пример индекса исходных задач.


### `data/source_index/source_groups.example.json`

Назначение:

- пример группировки сходных задач.


### `data/templates/README.md`

Назначение:

- описание каталога формализованных шаблонов.


### `data/templates/arithmetic/README.md`

Назначение:

- описание арифметических семейств шаблонов.


### `data/templates/arithmetic/sample_addition_template.example.json`

Назначение:

- пример арифметического шаблона.


### `data/templates/geometry/README.md`

Назначение:

- описание геометрических шаблонов.


### `data/templates/geometry/sample_segment_template.example.json`

Назначение:

- пример геометрического шаблона.


### `data/templates/time/README.md`

Назначение:

- описание шаблонов задач на время.


### `data/templates/time/sample_weekday_template.example.json`

Назначение:

- пример шаблона календарной задачи.


### `data/templates/logic/README.md`

Назначение:

- описание логических шаблонов.


### `data/templates/logic/sample_logic_template.example.json`

Назначение:

- пример логического шаблона.


### `data/templates/combinatorics/README.md`

Назначение:

- описание комбинаторных шаблонов.


### `data/templates/combinatorics/sample_product_rule_template.example.json`

Назначение:

- пример комбинаторного шаблона.


### `data/entities/README.md`

Назначение:

- описание словарей сущностей и ролей.


### `data/entities/roles.example.json`

Назначение:

- пример списка ролей и совместимости типов сущностей.


### `data/entities/characters/README.md`

Назначение:

- описание словаря персонажей.


### `data/entities/characters/sample_character.example.json`

Назначение:

- пример записи персонажа.


### `data/entities/locations/README.md`

Назначение:

- описание словаря локаций.


### `data/entities/locations/sample_location.example.json`

Назначение:

- пример записи локации.


### `data/entities/objects/README.md`

Назначение:

- описание словаря предметов.


### `data/entities/objects/sample_object.example.json`

Назначение:

- пример записи предмета.


### `data/language/README.md`

Назначение:

- описание языковых словарей и правил.


### `data/language/verbs/README.md`

Назначение:

- описание словаря глагольных рамок.


### `data/language/verbs/sample_verb_frame.example.json`

Назначение:

- пример записи глагольной рамки.


### `data/language/prepositions/README.md`

Назначение:

- описание правил предлогов и падежей.


### `data/language/prepositions/sample_preposition_rule.example.json`

Назначение:

- пример правила предлога.


### `data/language/function_words/README.md`

Назначение:

- описание служебных слов и коротких связок.


### `data/language/function_words/sample_function_words.example.json`

Назначение:

- пример словаря служебных слов.


### `data/language/agreement_rules/README.md`

Назначение:

- описание правил согласования.


### `data/language/agreement_rules/sample_agreement_rule.example.json`

Назначение:

- пример формального правила согласования.


## Папка `problemgen/`

### `problemgen/README.md`

Назначение:

- верхнеуровневое описание кодового слоя генератора.


### `problemgen/app.py`

Назначение:

- текущий оркестратор генерации.

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

### `problemgen/core/README.md`

Назначение:

- описание того, какие общие модели должны жить в `core/`.


### `problemgen/core/models.py`

Назначение:

- текущие общие модели генератора.


### `problemgen/core/difficulty.py`

Назначение:

- текущие уровни сложности.


### `problemgen/core/themes.py`

Назначение:

- текущий словарь тем и сущностей, который в будущем должен мигрировать в `data/` и `problemgen/entities/`.


### `problemgen/core/story_worlds.py`

Назначение:

- единый каталог сюжетных миров, локаций и персонажей;
- подготовка `StoryContext` для конкретной задачи.

Ключевые сущности:

- `StoryWorld`
- `StoryContext`
- `STORY_WORLDS`
- `sample_story_context(...)`


## Папка `problemgen/catalog/`

### `problemgen/catalog/README.md`

Назначение:

- описание будущего слоя каталога шаблонов.


### `problemgen/catalog/__init__.py`

Назначение:

- каркас пакета каталога;
- хранит обязательный docstring-контракт.


## Папка `problemgen/entities/`

### `problemgen/entities/README.md`

Назначение:

- описание будущего слоя работы с сущностями.


### `problemgen/entities/__init__.py`

Назначение:

- каркас пакета сущностей.


## Папка `problemgen/language/`

### `problemgen/language/README.md`

Назначение:

- описание будущего основного языкового слоя.


### `problemgen/language/morphology/README.md`

Назначение:

- описание будущего слоя морфологии.


### `problemgen/language/syntax/README.md`

Назначение:

- описание будущего слоя синтаксических рамок.


### `problemgen/language/renderer/README.md`

Назначение:

- описание будущего рендеринга текста.


### `problemgen/language/validators/README.md`

Назначение:

- описание будущих языковых валидаторов.


## Папка `problemgen/generation/`

### `problemgen/generation/README.md`

Назначение:

- описание будущего конвейера генерации.


### `problemgen/generation/selection/README.md`

Назначение:

- описание выбора шаблона.


### `problemgen/generation/numbers/README.md`

Назначение:

- описание генерации числовых параметров.


### `problemgen/generation/binding/README.md`

Назначение:

- описание связывания ролей, сущностей и слотов.


### `problemgen/generation/assembly/README.md`

Назначение:

- описание сборки структурированного экземпляра задачи.


## Папка `problemgen/io/`

### `problemgen/io/README.md`

Назначение:

- описание будущего слоя чтения и записи данных.


## Папка `problemgen/russian/`

### `problemgen/russian/README.md`

Назначение:

- фиксирует, что `problemgen/russian/` — переходный совместимый слой.


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

### `problemgen/domains/README.md`

Назначение:

- описывает роль доменных адаптеров.


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


### `problemgen/domains/olympiad_logic/domain.py`

Назначение:

- доменный генератор олимпиадных логических задач.


### `problemgen/domains/olympiad_logic/templates.py`

Назначение:

- шаблоны олимпиадных задач:
  `digit_erasing`, `birds_count`, `three_numbers_same_suffix`, `shared_payment_debt`.


### `problemgen/domains/olympiad_logic/solvers.py`

Назначение:

- вычисление ответов для олимпиадных шаблонов.


### `problemgen/domains/olympiad_logic/validators.py`

Назначение:

- проверка корректности параметров и ответов для олимпиадных шаблонов.


## Папка `problemgen/web/`

### `problemgen/web/README.md`

Назначение:

- описывает роль web-слоя.


### `problemgen/web/server.py`

Назначение:

- локальный HTTP-сервер и HTML-слой.


## Папка `frontend/`

### `frontend/README.md`

Назначение:

- объясняет границы браузерного UI.


### `frontend/styles.css`

Назначение:

- стили локального сайта.


### `frontend/app.js`

Назначение:

- интерактивное обновление формы сайта.


## Папка `scripts/`

### `scripts/README.md`

Назначение:

- правила для ручных entry point-файлов.


### `scripts/run_problemgen.py`

Назначение:

- основной launcher модульной архитектуры.


### `scripts/legacy_simple_generator.py`

Назначение:

- ранний автономный генератор задач;
- полезен как простая standalone-версия без веб-слоя и доменной архитектуры.


### `scripts/generate_friendship_class.py`

Назначение:

- генерирует 1000 задач про класс, дружбу и парты;
- использует единый слой миров, персонажей и локаций;
- сохраняет итог в `outputs/friendship_class/1000_zadach.json`.

Ключевые сущности:

- `plural(...)`
- `build_problem(...)`
- `main()`


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


### `outputs/friendship_class/1000_zadach.json`

Назначение:

- пример JSON-выгрузки набора задач про класс и дружбу.


### `outputs/generated/README.md`

Назначение:

- фиксирует место для новых runtime-выгрузок.


## Папка `tests/`

### `tests/README.md`

Назначение:

- верхнеуровневые правила для тестов.


### `tests/unit/README.md`

Назначение:

- правила и примеры unit-тестов.


### `tests/integration/README.md`

Назначение:

- правила и примеры integration-тестов.


### `tests/golden/README.md`

Назначение:

- описание golden-наборов для регрессии текста и JSON.


### `tests/fixtures/README.md`

Назначение:

- описание тестовых входных данных.


### `tests/test_story_worlds.py`

Назначение:

- проверяет корректность общего слоя сюжетных миров.


### `tests/test_olympiad_logic.py`

Назначение:

- проверяет генерацию олимпиадных шаблонов и `story metadata`.
