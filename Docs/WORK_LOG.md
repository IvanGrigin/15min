# Журнал работ

## 2026-07-15

### Авторские шаблоны группы G: планиметрия и измерения

Что сделано:

- заменены 108 bridge-заглушек листьев G01–G12 двенадцатью авторскими runtime-шаблонами; в ворклисте отмечены `done` все 188 задач группы;
- G01 возвращает составной ответ «сторона, площадь» (`answer_type = multi`);
- добавлены стратегии `geometry_g01_*`–`geometry_g12_*`, все они дают целые параметры и ответы; G07 явно переводит дм² в см², G11 — литры в высоту слоя;
- добавлены helpers `count_integer_rectangle_sides` (G05) и `grid_square_count` (G08); их результаты независимо сверены перебором в тестах.

Измененные файлы:

- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `problemgen/generation/template_generator.py`
- `tests/test_template_generator.py`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет.

Проверки:

- `python3 -m unittest discover -s tests` — 43 теста, OK;
- вручную сгенерировано по экземпляру каждого листа G01–G12; ответы G05/G08 дополнительно сверены независимым перебором.

Заметки для следующего агента:

- bridge-записей с `source_tree_leaf` G01–G12 больше нет; следующий свободный тематический блок следует вести в отдельном worktree и ветке.

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


## 2026-07-09

### Домен arithmetic: система морфологических шаблонов + словарь существительных в JSON

Что сделано:

- добавлен новый домен `problemgen/domains/arithmetic/` с 6 шаблонами классических задач;
- реализован движок шаблонов `problemgen/russian/template_engine.py` со слотами `{key:case}`, `{key:count,numkey}`, `{key:agree,numkey}`;
- добавлена структура `RussianNoun` с 12 явными падежными формами в `problemgen/russian/inflection.py`;
- добавлена поддержка переопределения форм счёта (`count_one/few/many`) для нестандартных слов;
- создана JSON-библиотека существительных `data/language/nouns/russian_nouns.json` на 100 слов;
- `problemgen/russian/noun_dict.py` переведён на загрузку из JSON — Python-код больше не содержит словарных данных;
- добавлен демо-скрипт `scripts/demo_arithmetic.py`;
- добавлена документация `Docs/RUSSIAN_TEMPLATES.md`.

Измененные файлы:

- `problemgen/russian/inflection.py` — добавлены поля `count_one/few/many`
- `problemgen/russian/noun_dict.py` — полностью переписан: загрузка из JSON вместо Python-констант
- `problemgen/russian/__init__.py` — добавлены экспорты
- `problemgen/domains/__init__.py` — добавлен `ArithmeticDomain`
- `DOCUMENTATION.md` — добавлен домен arithmetic и обновлена навигация
- `Docs/FILE_INDEX.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `data/language/nouns/russian_nouns.json` — 100 существительных с полными парадигмами
- `data/language/nouns/README.md`
- `problemgen/russian/template_engine.py`
- `problemgen/domains/arithmetic/__init__.py`
- `problemgen/domains/arithmetic/domain.py`
- `problemgen/domains/arithmetic/templates.py`
- `problemgen/domains/arithmetic/solvers.py`
- `Docs/RUSSIAN_TEMPLATES.md`
- `scripts/demo_arithmetic.py`

Проверки:

- `python3 -c "from problemgen.russian.noun_dict import NOUNS; print(len(NOUNS))"` → 100
- `python3 scripts/demo_arithmetic.py` — все 6 шаблонов генерируются корректно
- Морфология: год/лет, мороженых, человек/человека/человек — правильно

Заметки для следующего агента:

- чтобы добавить новое существительное, достаточно добавить запись в `data/language/nouns/russian_nouns.json`;
- для нестандартных форм счёта (типа мороженое, лет) использовать поле `count_forms: [one, few, many]`;
- шаблоны задач — в `problemgen/domains/arithmetic/templates.py`, туда же добавлять новые;
- `data/language/nouns/README.md` содержит инструкцию по добавлению слов.


### JSON-шаблоны листов с задачами и универсальный рендер

Что сделано:

- добавлен новый каталог `data/templates/worksheets/` для JSON-шаблонов листов;
- создан готовый шаблон `worksheet_5_tasks.json` с полями `Фамилия`, `Имя`, датой, 5 слотами задач и правой панелью под изображение и QR-код;
- реализован `problemgen/io/worksheet_renderer.py`;
- рендер понимает bundle-формат модульного генератора и простой список задач;
- добавлен ручной entry point `scripts/render_worksheet.py`;
- добавлены unit-тесты на загрузку шаблона, чтение задач и понятные ошибки;
- обновлена навигационная документация.

Измененные файлы:

- `README.md`
- `DOCUMENTATION.md`
- `data/templates/README.md`
- `problemgen/io/README.md`
- `problemgen/io/__init__.py`
- `scripts/README.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `data/templates/worksheets/README.md`
- `data/templates/worksheets/worksheet_5_tasks.json`
- `problemgen/io/worksheet_renderer.py`
- `scripts/render_worksheet.py`
- `tests/test_worksheet_renderer.py`
- `Docs/WORKSHEET_TEMPLATES.md`

Проверки:

- добавлены unit-тесты для нового рендера;
- ожидается ручной прогон `scripts/render_worksheet.py` на реальном JSON-наборе задач.

Заметки для следующего агента:

- не смешивать генерацию математики и слой визуального оформления;
- новые листовые шаблоны добавлять в `data/templates/worksheets/`, а не хардкодить координаты в Python;
- если понадобится другой лист, расширять JSON и универсальный рендер, а не делать отдельный одноразовый скрипт.


### Готовый пример листа с 5 арифметическими задачами

Что сделано:

- добавлен файл `outputs/generated/worksheet_5_math_problems_example.json`;
- в нем сохранен готовый пример с 5 арифметическими задачами для шаблона `worksheet_5_tasks.json`;
- пример совместим с `scripts/render_worksheet.py`, потому что использует поле `problems[*].problem_text`;
- документация по шаблонам обновлена ссылкой на этот пример.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORKSHEET_TEMPLATES.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `outputs/generated/worksheet_5_math_problems_example.json`

Проверки:

- структура JSON проверена вручную;
- формат входа согласован с правилами `problemgen/io/worksheet_renderer.py`.

Заметки для следующего агента:

- если нужен еще один готовый лист, лучше создавать новый JSON-артефакт в `outputs/generated/`, а не менять сам шаблон оформления;
- шаблон `data/templates/worksheets/worksheet_5_tasks.json` должен оставаться переиспользуемым и не содержать конкретные задачи.


### Шаблон листа с пустыми полями, дефолтными assets и сайт генерации

Что сделано:

- шаблон `worksheet_5_tasks.json` обновлен под пустые линии после `Фамилия` и `Имя`;
- из обязательных плейсхолдеров убраны `{{surname}}` и `{{name}}`;
- добавлен блок `assets.defaults` с путями к `assets/logo.png` и `assets/qr.png`;
- рендерер научен брать дефолтные assets из шаблона и рисовать `line`-элементы в заголовке;
- `ArithmeticDomain` зарегистрирован в общем каталоге `problemgen/app.py`;
- добавлен новый orchestration-слой `problemgen/worksheet/service.py`;
- добавлен локальный сайт `problemgen/web/worksheet_site.py` и launcher `scripts/run_site.py`;
- добавлены frontend-файлы `frontend/worksheet_site.css` и `frontend/worksheet_site.js`;
- создана документация `Docs/WEB_GENERATION.md`;
- пример student JSON и тесты обновлены под новую модель шапки без программной подстановки имени.

Измененные файлы:

- `README.md`
- `DOCUMENTATION.md`
- `scripts/README.md`
- `frontend/README.md`
- `problemgen/web/README.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`
- `Docs/WORKSHEET_TEMPLATES.md`
- `outputs/generated/worksheet_5_math_problems_example.json`
- `tests/test_worksheet_renderer.py`
- `problemgen/app.py`
- `problemgen/io/worksheet_renderer.py`
- `data/templates/worksheets/worksheet_5_tasks.json`

Новые файлы:

- `assets/README.md`
- `assets/logo.png`
- `assets/qr.png`
- `problemgen/worksheet/__init__.py`
- `problemgen/worksheet/README.md`
- `problemgen/worksheet/service.py`
- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.css`
- `frontend/worksheet_site.js`
- `scripts/run_site.py`
- `tests/test_worksheet_service.py`
- `Docs/WEB_GENERATION.md`

Проверки:

- ожидается прогон unit-тестов для `worksheet_renderer` и `worksheet_service`;
- ожидается ручной прогон CLI-рендера с дефолтными assets;
- ожидается ручная проверка `POST /generate` и скачивания PDF через новый сайт.

Заметки для следующего агента:

- новый сайт не должен генерировать задачи во frontend;
- список сложностей 1–10 валидируется в `problemgen/worksheet/service.py`;
- если позже появятся другие типы листов, лучше расширять `problemgen/worksheet/` и `data/templates/worksheets/`, а не дублировать сайт и рендер в новых скриптах.


### Дерево корпуса задач по темам и сложности

Дата:

- 2026-07-09

Что сделано:

- создан отдельный навигационный индекс для `Docs/all_tasks_all_files.md`;
- корпус задач разложен по крупным математическим темам;
- внутри каждой темы добавлено деление на `easy`, `medium`, `hard`;
- исходный файл с задачами не изменялся.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `data/source_index/all_tasks_tree_by_theme_and_difficulty.md`

Проверки:

- вручную проверено, что новый индекс лежит в правильном слое `data/source_index/`;
- вручную проверено, что `Docs/all_tasks_all_files.md` не редактировался.

Заметки для следующего агента:

- этот файл является тематической картой корпуса, а не заменой исходных задач;
- если понадобится поштучная разметка задач, ее нужно делать отдельным JSON-индексом с `source_ref`;
- для новых генераторов удобно сначала выбирать ветку в этом дереве, а затем уже выделять конкретный шаблон.


### HTML-страница для просмотра дерева задач

Дата:

- 2026-07-09

Что сделано:

- создана локальная HTML-страница для удобного просмотра дерева задач;
- темы выведены в виде карточек;
- добавлен фильтр по уровням `easy`, `medium`, `hard`;
- сохранена связь со структурным индексом в `data/source_index/`.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `outputs/generated/all_tasks_tree_view.html`

Проверки:

- вручную проверена корректность пути и структуры HTML-файла;
- визуальная логика страницы собрана без изменения исходного корпуса задач.

Заметки для следующего агента:

- это обзорный артефакт для чтения человеком, а не источник данных для генераторов;
- если позже появится автоматическая сборка таких страниц, источником должен оставаться `data/source_index/`, а не HTML.


### Интерактивное дерево для корпуса задач

Дата:

- 2026-07-10

Что сделано:

- страница `all_tasks_tree_view.html` переделана из статического набора карточек в настоящее дерево;
- добавлены раскрывающиеся ветки `theme -> branch`;
- добавлена правая панель, которая обновляется по клику на выбранный узел;
- добавлены поиск, `Expand all` и `Collapse all`.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`
- `outputs/generated/all_tasks_tree_view.html`

Новые файлы:

- нет

Проверки:

- логика дерева проверена визуально по структуре HTML и JavaScript;
- исходный индекс `data/source_index/all_tasks_tree_by_theme_and_difficulty.md` не изменялся.

Заметки для следующего агента:

- данные дерева пока зашиты в самой HTML-странице;
- если позже понадобится автоматическая синхронизация, разумнее генерировать HTML из `data/source_index/`, а не редактировать две структуры вручную.


### Статичные JSON-шаблоны и выбор тем для листа

Дата:

- 2026-07-12

Что сделано:

- добавлен каталог `data/templates/problem_templates.json` с девятью стартовыми неизменяемыми шаблонами;
- добавлены загрузка каталога, безопасное вычисление формул, генерация чисел и рендер плейсхолдеров;
- ученический лист теперь принимает пять пар `module` и `difficulty`, а ответы вместе с переменными сохраняются отдельно;
- сайт получил выбор темы для каждой задачи, `GET /api/modules` и новый контракт `POST /generate`;
- старый режим `difficulties` сохранён для обратной совместимости.

Измененные файлы:

- `data/templates/worksheets/worksheet_5_tasks.json`
- `problemgen/worksheet/service.py`
- `problemgen/worksheet/__init__.py`
- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.js`
- `scripts/generate_worksheet.py`
- `scripts/README.md`
- `Docs/WEB_GENERATION.md`
- `Docs/WORKSHEET_TEMPLATES.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `data/templates/problem_templates.json`
- `problemgen/catalog/problem_templates.py`
- `problemgen/generation/template_generator.py`
- `scripts/generate_problem_from_template.py`
- `scripts/generate_problem_set.py`
- `tests/test_template_generator.py`
- `Docs/PROBLEM_TEMPLATES.md`

Проверки:

- JSON-каталог проверен через PowerShell `ConvertFrom-Json`;
- `git diff --check` не нашёл ошибок форматирования;
- `python -m unittest tests.test_template_generator tests.test_worksheet_renderer tests.test_worksheet_service` — 20 тестов пройдены;
- создан проверочный лист из пяти тем: `worksheet_20260712_201433.pdf`, отдельные student и answers JSON;
- `GET /api/modules` вернул восемь модулей, а `POST /generate` успешно создал лист по пяти переданным темам;
- PNG-предпросмотр подтвердил пустые поля фамилии и имени, пять задач с разделителями, логотип и QR-код без ответов на листе.

Заметки для следующего агента:

- новые формулировки добавлять только в JSON-каталог, не в Python;
- если нужен новый математический способ подбора чисел, добавить общую `number_strategy` и тест для неё;
- `Docs/all_tasks_all_files.md` не изменялся.


### Уточнение контракта сайта шаблонных задач

Дата:

- 2026-07-12

Что сделано:

- `POST /generate` теперь возвращает поле `worksheet_file` вместе с существующим `filename`;
- проверка `items` теперь отсекает пару `module` + `difficulty`, если для нее нет подходящего статичного шаблона;
- обработка занятого порта сайта учитывает Windows-код `10048`;
- документация API обновлена под новый ответ и ошибку неподходящей сложности.

Измененные файлы:

- `problemgen/worksheet/service.py`
- `problemgen/web/worksheet_site.py`
- `tests/test_template_generator.py`
- `Docs/WEB_GENERATION.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет

Проверки:

- добавлен unit-тест на отказ при неподходящей сложности для выбранного модуля;
- полный прогон тестов нужно выполнить после правок.

Заметки для следующего агента:

- frontend продолжает пользоваться `download_url`, поэтому добавление `worksheet_file` обратно совместимо;
- новые endpoint-поля лучше добавлять без удаления старых, пока сайт и CLI используются параллельно.


## 2026-07-12

### Реестр стратегий чисел, кэш каталога и защита от вырожденных отношений

Задача:

- убедиться, что при росте числа шаблонов архитектура генератора не расползается, и устранить мелкие дефекты.

Что сделано:

- цепочка `if/elif` в `_numbers` заменена на реестр `_NUMBER_STRATEGIES` (dict имя → функция) с декоратором `@_number_strategy`; добавлен `registered_strategies()`;
- каталог шаблонов кэшируется через `functools.lru_cache` по ключу (путь, `st_mtime_ns`) — читается один раз, но перечитывается после правки файла; `load_template_catalog` отдаёт копию;
- стратегия `ratio_sum` теперь гарантирует `ratio_a > ratio_b` (отношение не вырождается в 1:1);
- в шаблоне `ratio_berries_001` вопрос «досталось первому персонажу» заменён на грамматически корректное «Сколько ягод в большей части?» (склонения имён в системе нет);
- добавлен пакетный `tests/__init__.py`, чтобы документированная команда `python -m unittest tests.test_template_generator` работала;
- добавлены тесты: все стратегии из JSON зарегистрированы; отношение никогда не вырождено;
- в `Docs/PROBLEM_TEMPLATES.md` добавлен раздел «Масштабирование».

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `problemgen/catalog/problem_templates.py`
- `data/templates/problem_templates.json`
- `tests/test_template_generator.py`
- `Docs/PROBLEM_TEMPLATES.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `tests/__init__.py`

Проверки:

- `python -m unittest tests.test_template_generator` — 10 тестов, OK;
- ручная генерация по всем модулям и по `ratios` с разными сидами — математика и текст корректны;
- проверено попадание в кэш каталога (2 hits из 3 вызовов).

Заметки для следующего агента:

- новый тип математики = одна функция с `@_number_strategy(...)` + JSON-запись; новый сюжет того же типа = только JSON;
- предсуществующий баг: `tests/test_worksheet_renderer.py` (2 теста) падает из-за отсутствующей фикстуры `outputs/friendship_class/1000_zadach.json` — к шаблонам отношения не имеет, но стоит починить отдельно.


### Починка тестов рендерера: фикстуры вместо генерируемых артефактов

Задача:

- убрать зависимость `tests/test_worksheet_renderer.py` от несуществующих на чистом клоне файлов `outputs/generated/counting.json` и `outputs/friendship_class/1000_zadach.json`.

Что сделано:

- добавлены самодостаточные фикстуры `tests/fixtures/problems_bundle.json` (формат `{header, problems}` из 5 задач) и `tests/fixtures/problems_plain_list.json` (plain-массив из 12 объектов с `condition`);
- два теста-загрузчика переведены с путей в `outputs/` на эти фикстуры.

Измененные файлы:

- `tests/test_worksheet_renderer.py`
- `Docs/FILE_INDEX.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `tests/fixtures/problems_bundle.json`
- `tests/fixtures/problems_plain_list.json`

Проверки:

- `python -m unittest discover -s tests` — 32 теста, OK (ранее 2 падали).

Заметки для следующего агента:

- тесты рендерера больше не зависят от генерируемых артефактов `outputs/`; новые проверки форматов задач опирай на `tests/fixtures/`, а не на вывод скриптов.


## 2026-07-13

### Production-дерево для будущих JSON-шаблонов

Задача:

- на основе `math_problem_tree_100_themes.md`, `math_problem_tree_full_coverage.md`, `template_coverage_report.md` и текущего `problem_templates.json` создать более полезное дерево для разработки сложных шаблонов.

Что сделано:

- добавлен файл `data/source_index/math_problem_tree_template_ready.md`;
- все 100 тем переведены в формат `theme -> generator module -> template family -> variables -> answer model -> minimum actions`;
- добавлены правила: шаблоны должны быть статичными JSON-записями, с constraints, formula/validator и минимумом действий для решения;
- добавлен приоритет внедрения `P1`-`P4`, где `P1` связан с уже существующими модулями `problem_templates.json`;
- добавлен пример JSON-шаблона в стиле текущего каталога, но с более сложной задачей на встречное движение с задержкой.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `data/source_index/math_problem_tree_template_ready.md`

Проверки:

- проверено наличие трех входных файлов в `docs/`;
- исходный read-only корпус `Docs/all_tasks_all_files.md` не изменялся;
- код генератора и `data/templates/problem_templates.json` не менялись.

Заметки для следующего агента:

- следующий практический шаг: взять `P1`-листья из нового дерева и расширить `data/templates/problem_templates.json` сложными шаблонами, добавляя новые `number_strategy` только там, где формулы текущего генератора недостаточно.


### Production-шаблоны из template-ready дерева

Задача:

- использовать `data/source_index/math_problem_tree_template_ready.md` как основу для расширения рабочего JSON-каталога математических задач.

Что сделано:

- `data/templates/problem_templates.json` расширен с 9 до 19 шаблонов;
- добавлены более сложные шаблоны с несколькими действиями решения:
  `ages_joining_group_001`, `ratio_transfer_001`, `heads_and_legs_removed_001`,
  `joint_work_delay_001`, `round_robin_missing_001`, `paint_cube_unpainted_001`,
  `movement_two_stage_001`, `opposite_motion_delay_001`,
  `factor_shortcut_compare_001`, `price_system_two_receipts_001`;
- в `problemgen/generation/template_generator.py` добавлены соответствующие
  `number_strategy`, которые подбирают целочисленные параметры и ответы;
- обновлена документация `Docs/PROBLEM_TEMPLATES.md`.

Измененные файлы:

- `data/templates/problem_templates.json`
- `problemgen/generation/template_generator.py`
- `Docs/PROBLEM_TEMPLATES.md`
- `Docs/FILE_INDEX.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет

Проверки:

- `ConvertFrom-Json` подтвердил валидность JSON-каталога;
- `python -m unittest tests.test_template_generator` — 10 тестов, OK;
- `python -m unittest discover -s tests` — 32 теста, OK.

Заметки для следующего агента:

- новые модули `opposite_motion`, `factor_shortcut`, `price_system` теперь появятся в списке доступных модулей сайта через `list_modules()`;
- если нужно добавлять следующие темы, начинать с приоритета `P2` в `math_problem_tree_template_ready.md`.


### Дополнительные 40 шаблонов по production-дереву

Задача:

- добавить ещё 40 JSON-шаблонов на основе `data/source_index/math_problem_tree_template_ready.md`, сохранив совместимость с текущим генератором.

Что сделано:

- `data/templates/problem_templates.json` расширен с 19 до 59 шаблонов;
- новые шаблоны добавлены как варианты production-семейств:
  `ages_joining_group`, `ratio_transfer`, `heads_and_legs_removed`,
  `joint_work_delay`, `round_robin_missing`, `paint_cube_unpainted`,
  `movement_two_stage`, `opposite_motion_delay`, `factor_shortcut_compare`,
  `price_system_two_receipts`;
- Python-логика не расширялась: все 40 шаблонов используют уже зарегистрированные
  `number_strategy`, поэтому рост каталога остался data-driven.
- формулировки с переменными числами приведены к устойчивым вариантам через
  `шт.`, `чел.` и нейтральные математические обороты, чтобы случайные числа не
  ломали падежи.

Измененные файлы:

- `data/templates/problem_templates.json`
- `Docs/PROBLEM_TEMPLATES.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет

Проверки:

- `ConvertFrom-Json` подтвердил валидность JSON-каталога и 59 шаблонов;
- `python -m unittest tests.test_template_generator` — 10 тестов, OK;
- `python -m unittest discover -s tests` — 32 теста, OK.

Заметки для следующего агента:

- следующая волна шаблонов может либо продолжать добавлять JSON-варианты существующих стратегий, либо взять новые листья `P2/P3` и добавить для них отдельные валидаторы.


### Массовое bridge-покрытие дерева шаблонов

Задача:

- добавить около 900 шаблонов, чтобы почти каждый математический leaf из
  `data/source_index/math_problem_tree_template_ready.md` имел место в JSON-каталоге.

Что сделано:

- добавлен `scripts/expand_problem_templates_from_tree.py`;
- скрипт читает 100 leaf-ID из дерева и создает по 9 bridge-шаблонов на каждый;
- `data/templates/problem_templates.json` расширен с 59 до 959 шаблонов;
- все массовые записи имеют `template_id` вида `tree_a01_ratio_transfer_02`;
- все массовые записи вынесены в модули `tree_*`, чтобы не ломать старые ручные
  модули и их тестовые ожидания;
- для связи с деревом добавлены поля `source_tree_leaf` и `source_tree_module`;
- скрипт сделан идемпотентным: повторный запуск обновляет существующие
  bridge-записи, но не добавляет дубликаты.

Измененные файлы:

- `data/templates/problem_templates.json`
- `Docs/PROBLEM_TEMPLATES.md`
- `Docs/WORK_LOG.md`
- `scripts/README.md`

Новые файлы:

- `scripts/expand_problem_templates_from_tree.py`

Проверки:

- `ConvertFrom-Json` подтвердил валидность JSON-каталога и 959 шаблонов;
- найдено 900 записей с `source_tree_leaf`;
- найдено 900 записей с `template_id` вида `tree_*`;
- `python -m unittest tests.test_template_generator` — 10 тестов, OK;
- `python -m unittest discover -s tests` — 32 теста, OK;
- CLI успешно сгенерировал задачи из `tree_expression_value` и
  `tree_cryptarithm_missing_digits`.

Заметки для следующего агента:

- это scaffold/bridge-покрытие, а не финальная ручная библиотека из 900
  уникальных олимпиадных моделей;
- если конкретный leaf становится важным, заменить его bridge-шаблоны на точные
  тематические шаблоны и при необходимости добавить новую `number_strategy`.


## 2026-07-14

### Ворклист под точный шаблон и формулу для каждой из 2121 задач корпуса

Задача:

- подготовить основу для будущей работы: под каждую задачу корпуса завести отдельный слот под свой `template_text`, `number_strategy` и `answer_formula`, чтобы можно было воспроизводить и оригинальные, и похожие задачи.

Что сделано:

- проверено покрытие: дерево `task_tree` разбивает корпус на 100 листьев без потерь (все 2121 ID покрыты ровно один раз), каталог содержит 959 шаблонов (900 bridge + 59 ручных), но bridge-шаблоны — заглушки, часто не того типа;
- добавлен скрипт `scripts/build_per_task_template_worklist.py`: сводит текст задачи из корпуса с темой/сложностью из дерева и раскладывает по одному слоту на задачу; идемпотентен, не затирает заполненные вручную слоты;
- сгенерирован `data/source_index/per_task_template_worklist.json` — 2121 слот, все привязаны к листу; эвристика движка: 1527 `arithmetic_candidate`, 594 `needs_extension`;
- добавлена методичка `Docs/PER_TASK_TEMPLATE_PLAN.md` с порядком работы, двумя дорожками (арифметика на текущем движке vs расширение движка) и критерием завершённости.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `scripts/build_per_task_template_worklist.py`
- `data/source_index/per_task_template_worklist.json`
- `Docs/PER_TASK_TEMPLATE_PLAN.md`

Проверки:

- `python scripts/build_per_task_template_worklist.py` — 2121 задача, 2121 привязано к листу, 0 сделано;
- проверена целостность: id уникальны, диапазон 1..2121, все слоты шаблонов пусты (готовы к заполнению).

Заметки для следующего агента:

- это каркас, а не готовые шаблоны: заполнение `template_text`/`number_strategy`/`answer_formula` — предстоящая ручная работа по батчам (удобно — по одному `leaf_id`);
- 594 задачи `needs_extension` требуют расширения движка (целочисленные `//` `%` `**`, gcd, подсчёт цифр, `answer_type` = multi/text) — до этого их текст воспроизводим, но не ответ;
- отдельно открыт баг надёжности: 13/959 текущих шаблонов падают «вне constraints» на части сидов.


### Расширение движка ответа под needs_extension

Задача:

- разблокировать ~594 задачи `needs_extension`, дав движку возможность считать неарифметические ответы.

Что сделано:

- `evaluate_formula` расширен и остаётся безопасным: добавлены операторы `//`, `%`, `**` (показатель 0..64), белый список функций (`gcd, lcm, isqrt, comb, perm, digit_sum, count_digit, count_multiples, num_divisors, weekday_after`, `abs/min/max`), поддержка строк-констант; всё вне списка (`open`, `eval`) отклоняется;
- добавлены `answer_type = "multi"` (список ответов) и `"text"` (строка); `generate_problem_from_template` учитывает тип при проверке ответа; тип `answer` в `GeneratedTemplateProblem` расширен до `int | float | str | list`;
- добавлены 4 стратегии (`digit_count_range`, `gcd_pair`, `weekday_after`, `two_products`) и 4 эталонных шаблона в каталог: `digit_count_range_001`, `gcd_pair_001`, `weekday_after_001`, `two_products_compare_001` (каталог 959 -> 963);
- обновлён `Docs/PER_TASK_TEMPLATE_PLAN.md`: группа `needs_extension` теперь разблокирована, описан белый список и точка роста (`_FUNCTIONS`);
- тесты: расширенные операторы, ограничение степени, функции, multi/text, отказ не-белых вызовов, генерация 4 новых типов; обновлён общий тест под `answer_type`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `tests/test_template_generator.py`
- `Docs/PER_TASK_TEMPLATE_PLAN.md`
- `Docs/WORK_LOG.md`

Проверки:

- `python -m unittest discover -s tests` — 41 тест, OK;
- перекрёстно сверены ответы (`count_digit`, `gcd`) и типы (text/multi); 4 новых шаблона стабильны на 30 сидах × всех сложностях.

Заметки для следующего агента:

- УТОЧНЕНИЕ по надёжности: хрупких шаблонов не 13, а ~205 из 963 (в основном bridge tree_* на стратегиях `ratio_transfer`, `price_system_two_receipts`, `equal_payment` и др.) — они падают «вне constraints» на части сидов; штатный тест использует один сид на шаблон и это не ловит. Это pre-existing и требует отдельной чистки стратегий/constraints;
- следующий разумный шаг — заполнять ворклист батчами по темам, используя новые функции движка, и параллельно чинить хрупкие стратегии.


### Чистка хрупких стратегий и первый батч ворклиста

Задача:

- убрать хрупкость ~205 шаблонов (падения «вне constraints») и начать заполнять ворклист батчами по темам.

Что сделано:

- диагностика показала, что весь хвост создают 4 стратегии с едиными границами; исправлены у корня:
  - `heads_and_legs`: `ducks >= 2` → `heads >= 3`, `legs >= 8`;
  - `equal_payment`: множители подрезаны (total ≤ 20000, loan ≤ 30000, paid_2 ≤ 20000);
  - `ratio_transfer`: `multiplier >= 4` → `total >= 15`;
  - `price_system_two_receipts`: цена ≤ 290 → `total_1/total_2 ≤ 4640` (< самой тесной границы 5000);
- после правок широкий свип (963 шаблона × все сложности × 60 сидов) даёт 0 хрупких;
- добавлен тест-страж `test_no_template_is_fragile_across_seeds` (несколько сложностей × 6 сидов на шаблон, ~1.6s);
- заполнен первый батч ворклиста — тема «частота цифры» (11 задач, лист C04): шаблон + `count_digit(...)`, `status=done`, ответы сверены (напр. цифра 2 в 1..120 → 23).

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `tests/test_template_generator.py`
- `data/source_index/per_task_template_worklist.json`
- `Docs/WORK_LOG.md`

Проверки:

- `python -m unittest discover -s tests` — 42 теста, OK;
- свип на 60 сидов — 0 хрупких; билдер ворклиста идемпотентен (сделано: 11 сохраняется).

Заметки для следующего агента:

- шаблон стратегии — источник истины по границам; при добавлении шаблона держать constraints согласованными со стратегией, тест-страж это проверит;
- ворклист: 11/2121 done; следующие удобные батчи — прямые вычисления (A01), НОД/делимость, день недели, сравнение произведений — все уже поддержаны движком.


### Документация авторинга, разбивка на агентов, батч A04

Задача:

- начать замену 900 заглушек авторскими шаблонами, задокументировать процесс и раздать работу агентам.

Что сделано:

- добавлен хелпер `bigger_label` в белый список функций движка и стратегия `compare_triple_products`;
- лист A04 переведён на авторский шаблон `compare_triple_products_a04_001` (сравнение близких произведений, ответ `multi`): 9 заглушек `tree_a04` удалены, ответы сверены независимым расчётом; в ворклисте A04 отмечено 23 задачи → всего done 34/2121;
- написано полное руководство `Docs/TEMPLATE_AUTHORING_GUIDE.md` (анатомия шаблона, движок, правило стратегий, цикл замены заглушки, DoD);
- написан `Docs/AGENT_TASKS.md`: работа разбита на 11 групп тем (A–K, по агенту на группу), правила координации (ветка на агента, префиксы имён, маленькие батчи) и готовый промпт для запуска агента.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/FILE_INDEX.md`, `Docs/WORK_LOG.md`

Новые файлы:

- `Docs/TEMPLATE_AUTHORING_GUIDE.md`
- `Docs/AGENT_TASKS.md`

Проверки:

- `python -m unittest discover -s tests` — 42 теста, OK;
- A04: 3 генерации сверены (`bigger_label` + разность), тип задачи совпадает с корпусом.

Заметки для следующего агента:

- правка `problem_templates.json` даёт большой git --stat (git путается на почти одинаковых bridge-блоках) — семантически меняются только нужные шаблоны, это ожидаемо для машинного файла;
- дальше — по одному агенту на группу (см. `AGENT_TASKS.md`), приоритет A/C/D.
