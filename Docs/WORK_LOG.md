# Журнал работ

## Формат записи

Каждая новая запись должна содержать:

- дата;
- задача;
- что сделано;
- измененные файлы;
- новые файлы;
- проверки;
- заметки для следующего агента.


## 2026-07-06

### Инициализация агентской документации

Что сделано:

- добавлен `AGENTS.md` в корень проекта;
- создана папка `Docs/`;
- создан индекс файлов;
- создано смысловое дерево навигации;
- создан журнал работ;
- зафиксировано правило, что будущие агенты обязаны обновлять документацию после изменений.

Измененные файлы:

- `AGENTS.md`

Новые файлы:

- `Docs/README.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Проверки:

- структура файлов проверена вручную;
- документы согласованы с текущим составом проекта.

Заметки для следующего агента:

- перед новой работой сначала открыть `AGENTS.md`;
- после любого изменения обязательно дописать новую запись в этот журнал;
- если добавляется новый файл, его нужно вписать и в `Docs/FILE_INDEX.md`, и в `Docs/VECTOR_TREE.md`.


### Модульная архитектура генератора задач

Что сделано:

- `02.py` превращен в тонкий launcher новой архитектуры;
- добавлен пакет `problemgen/` с общим `CLI`, оркестратором и доменными блоками;
- вынесен отдельный модуль русского языка с несколькими файлами: словоформы, согласование, валидация;
- добавлены отдельные блоки задач `segments`, `counting`, `combinatorics`;
- старый сегментный монолит сохранен как совместимый модуль `problemgen/domains/segments/legacy_engine.py`;
- вынесен отдельный веб-слой `problemgen/web/server.py`;
- вынесен отдельный фронтенд `frontend/styles.css` и `frontend/app.js`;
- добавлена общая языковая проверка, которая записывает `language_issues` в итоговый `JSON`;
- обновлена навигационная документация под новую структуру.

Измененные файлы:

- `02.py`
- `DOCUMENTATION.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `problemgen/__init__.py`
- `problemgen/app.py`
- `problemgen/cli.py`
- `problemgen/core/__init__.py`
- `problemgen/core/models.py`
- `problemgen/core/difficulty.py`
- `problemgen/core/themes.py`
- `problemgen/russian/__init__.py`
- `problemgen/russian/lexicon.py`
- `problemgen/russian/agreement.py`
- `problemgen/russian/validator.py`
- `problemgen/domains/__init__.py`
- `problemgen/domains/base.py`
- `problemgen/domains/segments/__init__.py`
- `problemgen/domains/segments/domain.py`
- `problemgen/domains/segments/legacy_engine.py`
- `problemgen/domains/counting/__init__.py`
- `problemgen/domains/counting/domain.py`
- `problemgen/domains/counting/templates.py`
- `problemgen/domains/combinatorics/__init__.py`
- `problemgen/domains/combinatorics/domain.py`
- `problemgen/domains/combinatorics/templates.py`
- `problemgen/web/__init__.py`
- `problemgen/web/server.py`
- `frontend/styles.css`
- `frontend/app.js`

Проверки:

- `python3 -m py_compile 02.py problemgen/*.py problemgen/core/*.py problemgen/russian/*.py problemgen/domains/*.py problemgen/domains/segments/*.py problemgen/domains/counting/*.py problemgen/domains/combinatorics/*.py problemgen/web/*.py`
- `python3 02.py --domain counting --count 2 --difficulty-level medium --story-theme space --seed-mode fixed --seed 7 --output output/test_counting.json`
- `python3 02.py --domain combinatorics --count 2 --difficulty-level easy --story-theme cowboy --seed-mode fixed --seed 9 --output output/test_combinatorics.json`
- `python3 02.py --domain segments --count 2 --difficulty-level medium --story-theme ants --seed-mode fixed --seed 5 --output output/test_segments_modular.json`
- `python3 02.py --serve --host 127.0.0.1 --port 8011`
- `curl -I http://127.0.0.1:8011/`
- `curl -I http://127.0.0.1:8011/static/styles.css`
- `curl -v http://127.0.0.1:8011/`

Заметки для следующего агента:

- новые домены нужно добавлять через `problemgen/domains/` и регистрацию в `problemgen/app.py`;
- массовые исправления согласования слов делать в `problemgen/russian/`, а не по отдельным шаблонам;
- задачи на отрезки пока работают через `legacy_engine.py`, это промежуточный слой совместимости;
- итоговый `JSON` теперь финально переписывается после общей языковой проверки, даже если домен уже что-то сохранил раньше.


### Подготовка отдельного GitHub-репозитория

Что сделано:

- добавлен `.gitignore` для Python-кэша и выходных артефактов;
- документация обновлена под отдельный git-репозиторий проекта;
- проект подготовлен к публикации в отдельный GitHub-репозиторий `IvanGrigin/15min`.

Измененные файлы:

- `.gitignore`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `.gitignore`

Проверки:

- структура файлов проекта и состав артефактов проверены вручную перед инициализацией отдельного git-репозитория.

Заметки для следующего агента:

- `output/` и `__pycache__/` исключены из git;
- проект должен жить как отдельный репозиторий внутри `problems_15min_generator`, а не как часть родительского `Desktop`-репозитория.


## 2026-07-08

### Перестройка структуры проекта под рост числа генераторов

Что сделано:

- папка `Docs/` переименована в `docs/`;
- запускаемые файлы вынесены в `scripts/` с осмысленными именами;
- сгенерированные артефакты вынесены в `outputs/`;
- добавлены `README.md` для `scripts/`, `outputs/` и `tests/`;
- файл генератора дружеских задач перенастроен на сохранение в `outputs/friendship_class/1000_zadach.txt`;
- обновлены `AGENTS.md`, индекс файлов и навигационная документация под новую структуру.

Измененные файлы:

- `AGENTS.md`
- `README.md`
- `.gitignore`
- `DOCUMENTATION.md`
- `problemgen/domains/segments/legacy_engine.py`
- `docs/README.md`
- `docs/FILE_INDEX.md`
- `docs/VECTOR_TREE.md`
- `docs/WORK_LOG.md`
- `scripts/run_problemgen.py`
- `scripts/legacy_simple_generator.py`
- `scripts/generate_friendship_class.py`

Новые файлы:

- `scripts/README.md`
- `outputs/README.md`
- `tests/README.md`

Проверки:

- структура папок проверена вручную;
- пути к новым скриптам и выходным файлам сверены вручную;
- автоматический прогон не выполнялся в рамках этой перестройки.

Заметки для следующего агента:

- новые генераторы не класть в корень проекта;
- новые entry point-файлы создавать в `scripts/` и называть по смыслу;
- результаты генерации сохранять в `outputs/` по подпапкам доменов или сценариев;
- при следующем изменении запусков стоит добавить автоматические тесты в `tests/`.


### Перевод генератора дружбы в классе на JSON-выгрузку

Что сделано:

- `scripts/generate_friendship_class.py` переведен с текстовой выгрузки на JSON;
- каждая задача теперь сохраняется как объект с полями `id`, `condition`, `answer`;
- выходной файл изменен на `outputs/friendship_class/1000_zadach.json`;
- навигационная документация обновлена под новый формат результата.

Измененные файлы:

- `scripts/generate_friendship_class.py`
- `scripts/README.md`
- `outputs/README.md`
- `DOCUMENTATION.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет

Проверки:

- ожидается ручной прогон скрипта после изменения формата.

Заметки для следующего агента:

- для этого сценария итоговый артефакт теперь JSON, а не TXT;
- если понадобится другой JSON-формат, менять его нужно в `build_problem(...)` и `main()`.


### Единый слой сюжетных миров и персонажей

Что сделано:

- добавлен модуль `problemgen/core/story_worlds.py`;
- добавлен общий каталог `STORY_WORLDS` с русскоязычными мирами, локациями и персонажами;
- CLI расширен флагами `--story-world` и `--list-story-worlds`;
- `problemgen/app.py` теперь заранее создает `StoryContext` и передает его доменам через `options`;
- домены `counting` и `combinatorics` обновлены как пример использования общего сюжетного слоя;
- `scripts/generate_friendship_class.py` переведен на использование общего каталога миров;
- добавлена документация `Docs/STORY_WORLDS.md`;
- добавлены минимальные тесты для нового слоя.

Измененные файлы:

- `README.md`
- `DOCUMENTATION.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`
- `problemgen/cli.py`
- `problemgen/app.py`
- `problemgen/web/server.py`
- `problemgen/domains/counting/domain.py`
- `problemgen/domains/counting/templates.py`
- `problemgen/domains/combinatorics/domain.py`
- `problemgen/domains/combinatorics/templates.py`
- `scripts/generate_friendship_class.py`

Новые файлы:

- `problemgen/core/story_worlds.py`
- `Docs/STORY_WORLDS.md`
- `tests/test_story_worlds.py`

Проверки:

- ожидается прогон `--list-story-worlds`;
- ожидается прогон доменов `counting` и `combinatorics` с `--story-world`;
- ожидается запуск unit-тестов для `story_worlds`.

Заметки для следующего агента:

- новые генераторы не должны хранить свои отдельные списки миров и персонажей;
- если генератор использует сюжет, он должен брать его из `StoryContext`;
- legacy-домен `segments` пока оставлен с fallback-поведением без обязательной миграции.


### Новый домен олимпиадной логики

Что сделано:

- добавлен новый домен `problemgen/domains/olympiad_logic/`;
- в домен вынесены отдельные `templates.py`, `solvers.py`, `validators.py` и `domain.py`;
- реализованы 4 шаблона: `digit_erasing`, `birds_count`, `three_numbers_same_suffix`, `shared_payment_debt`;
- все шаблоны используют общий `StoryContext` вместо локальных списков персонажей;
- добавлены тесты на генерацию шаблонов и `story metadata`;
- обновлена навигационная документация под новый домен.

Измененные файлы:

- `README.md`
- `DOCUMENTATION.md`
- `Docs/STORY_WORLDS.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`
- `problemgen/app.py`
- `problemgen/domains/__init__.py`

Новые файлы:

- `problemgen/domains/olympiad_logic/__init__.py`
- `problemgen/domains/olympiad_logic/domain.py`
- `problemgen/domains/olympiad_logic/templates.py`
- `problemgen/domains/olympiad_logic/solvers.py`
- `problemgen/domains/olympiad_logic/validators.py`
- `tests/test_olympiad_logic.py`

Проверки:

- ожидается прогон CLI-команд для `olympiad_logic`;
- ожидается запуск unit-тестов.

Заметки для следующего агента:

- новые олимпиадные шаблоны добавлять в `problemgen/domains/olympiad_logic/templates.py`;
- вычисление ответов держать в `solvers.py`, а проверки в `validators.py`;
- сюжетные персонажи и локации не дублировать, а брать только из `problemgen/core/story_worlds.py`.


### Упрощение формулировок с персонажами и мирами

Что сделано:

- из текстов генераторов убраны неестественные конструкции вида `В локации ... персонажи ...`;
- персонажи теперь ставятся в более естественную позицию в начале условия;
- сюжетный мир оставлен в тексте задачи, а локация сохранена в `story metadata`.

Измененные файлы:

- `problemgen/domains/counting/templates.py`
- `problemgen/domains/combinatorics/templates.py`
- `problemgen/domains/olympiad_logic/templates.py`
- `scripts/generate_friendship_class.py`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет

Проверки:

- ожидается ручной прогон генераторов после правки формулировок.

Заметки для следующего агента:

- если сюжетные данные звучат неестественно в русском тексте, лучше упоминать мир в условии, а локацию оставлять в metadata.


### Исправление падежных форм в задачах про оплату

Что сделано:

- в шаблоне `shared_payment_debt` убраны формы вида `Мася дал Папус` и `вернуть Папус персонажу Мася`;
- косвенные падежи теперь строятся через слова `персонаж` и `персонажу`, а имена остаются в кавычках в начальной форме.

Измененные файлы:

- `problemgen/domains/olympiad_logic/templates.py`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет

Проверки:

- ожидается ручной прогон шаблона `shared_payment_debt`.

Заметки для следующего агента:

- если понадобится полноценное склонение имён персонажей, лучше делать отдельный слой морфологии, а не набор ручных исключений по шаблонам.


### Архитектурный blueprint для масштабирования шаблонов и русского языка

Что сделано:

- полностью переписан `AGENTS.md` под архитектурную работу будущих агентов;
- добавлены документы `Docs/ARCHITECTURE_BLUEPRINT.md`, `Docs/REPOSITORY_STRUCTURE.md` и `Docs/DATA_FLOW.md`;
- добавлен новый слой `data/` с подпапками для схем, таксономий, индекса исходных задач, шаблонов, сущностей и языковых словарей;
- добавлены примерные JSON-контракты для шаблона задачи, экземпляра задачи, сущности, глагольной рамки, ролей и таксономий;
- добавлены новые каркасные пакеты `problemgen/catalog/`, `problemgen/entities/`, `problemgen/language/`, `problemgen/generation/`, `problemgen/io/` с обязательными docstring и README;
- добавлены README в важные существующие каталоги, чтобы будущие агенты не удаляли структурные пояснения;
- обновлены `Docs/FILE_INDEX.md`, `Docs/VECTOR_TREE.md`, `README.md`, `DOCUMENTATION.md`, `outputs/README.md` и `tests/README.md`.

Измененные файлы:

- `AGENTS.md`
- `README.md`
- `DOCUMENTATION.md`
- `Docs/README.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`
- `outputs/README.md`
- `tests/README.md`

Новые файлы:

- `Docs/ARCHITECTURE_BLUEPRINT.md`
- `Docs/REPOSITORY_STRUCTURE.md`
- `Docs/DATA_FLOW.md`
- `data/README.md`
- `data/schemas/README.md`
- `data/schemas/task_template.example.json`
- `data/schemas/task_instance.example.json`
- `data/schemas/entity.example.json`
- `data/schemas/verb_lexeme.example.json`
- `data/taxonomy/README.md`
- `data/taxonomy/categories.example.json`
- `data/taxonomy/genres.example.json`
- `data/taxonomy/feature_flags.example.json`
- `data/taxonomy/difficulty_scale.example.json`
- `data/source_index/README.md`
- `data/source_index/tasks_index.example.json`
- `data/source_index/source_groups.example.json`
- `data/templates/README.md`
- `data/templates/arithmetic/README.md`
- `data/templates/arithmetic/sample_addition_template.example.json`
- `data/templates/geometry/README.md`
- `data/templates/geometry/sample_segment_template.example.json`
- `data/templates/time/README.md`
- `data/templates/time/sample_weekday_template.example.json`
- `data/templates/logic/README.md`
- `data/templates/logic/sample_logic_template.example.json`
- `data/templates/combinatorics/README.md`
- `data/templates/combinatorics/sample_product_rule_template.example.json`
- `data/entities/README.md`
- `data/entities/roles.example.json`
- `data/entities/characters/README.md`
- `data/entities/characters/sample_character.example.json`
- `data/entities/locations/README.md`
- `data/entities/locations/sample_location.example.json`
- `data/entities/objects/README.md`
- `data/entities/objects/sample_object.example.json`
- `data/language/README.md`
- `data/language/verbs/README.md`
- `data/language/verbs/sample_verb_frame.example.json`
- `data/language/prepositions/README.md`
- `data/language/prepositions/sample_preposition_rule.example.json`
- `data/language/function_words/README.md`
- `data/language/function_words/sample_function_words.example.json`
- `data/language/agreement_rules/README.md`
- `data/language/agreement_rules/sample_agreement_rule.example.json`
- `problemgen/README.md`
- `problemgen/core/README.md`
- `problemgen/domains/README.md`
- `problemgen/russian/README.md`
- `problemgen/web/README.md`
- `problemgen/catalog/__init__.py`
- `problemgen/catalog/README.md`
- `problemgen/entities/__init__.py`
- `problemgen/entities/README.md`
- `problemgen/language/__init__.py`
- `problemgen/language/README.md`
- `problemgen/language/morphology/__init__.py`
- `problemgen/language/morphology/README.md`
- `problemgen/language/syntax/__init__.py`
- `problemgen/language/syntax/README.md`
- `problemgen/language/renderer/__init__.py`
- `problemgen/language/renderer/README.md`
- `problemgen/language/validators/__init__.py`
- `problemgen/language/validators/README.md`
- `problemgen/generation/__init__.py`
- `problemgen/generation/README.md`
- `problemgen/generation/selection/__init__.py`
- `problemgen/generation/selection/README.md`
- `problemgen/generation/numbers/__init__.py`
- `problemgen/generation/numbers/README.md`
- `problemgen/generation/binding/__init__.py`
- `problemgen/generation/binding/README.md`
- `problemgen/generation/assembly/__init__.py`
- `problemgen/generation/assembly/README.md`
- `problemgen/io/__init__.py`
- `problemgen/io/README.md`
- `frontend/README.md`
- `outputs/generated/README.md`
- `tests/unit/README.md`
- `tests/integration/README.md`
- `tests/golden/README.md`
- `tests/fixtures/README.md`

Проверки:

- структура директорий и новых blueprint-файлов проверена вручную;
- JSON-примеры сверены вручную на синтаксис;
- код существующей рабочей логики не менялся;
- автоматический прогон генераторов не выполнялся, потому что работа была архитектурно-документационной.

Заметки для следующего агента:

- новые README и docstring-контракты нельзя молча удалять;
- новые словари, шаблоны и индексы нужно развивать в `data/`, а не прятать обратно в Python-константы;
- `problemgen/russian/` считать переходным слоем, а новые крупные языковые механизмы проектировать в `problemgen/language/`;
- `Docs/all_tasks_all_files.md` по-прежнему read-only.
