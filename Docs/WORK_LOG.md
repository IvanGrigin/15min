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


## 2026-07-15

### Восстановление тестового прогона после обновления каталога

Что сделано:

- из `data/templates/problem_templates.json` удалён служебный UTF-8 BOM, из-за которого стандартный JSON-загрузчик не мог прочитать каталог;
- ожидание веб-теста синхронизировано с актуальным текстом интерфейса «Выберите пять модулей».

Измененные файлы:

- `data/templates/problem_templates.json`
- `tests/test_worksheet_site.py`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет.

Проверки:

- полный `python3 -m unittest discover -s tests -p 'test_*.py'` запущен: BOM-ошибки устранены, но 8 проверок остаются красными из-за несовместимых ожиданий двух каталогов (`problem_templates.json` содержит 184 runtime-шаблона, а новые тесты ожидают 1528 записей `All_tasks_templates.json`);
- изолированная генерация олимпиадных модулей проходит.

Заметки для следующего агента:

- JSON-каталоги хранить в UTF-8 без BOM, так как их читают и `json.load`, и прямые `json.loads`.
- миграцию default-каталога и тестов на `All_tasks_templates.json` выполнять отдельной задачей: она меняет контракт сайта и старого runtime-генератора.


## 2026-07-15

### Интеграция и закрытие олимпиадной ветки

Что сделано:

- последняя неслитая ветка `olympiad/authoring` интегрирована в `main`;
- добавлены изолированный каталог олимпиадных шаблонов, памятка по треку и четыре стартовые стратегии;
- `generate_problem_from_template(...)` получил необязательный `catalog_path`, чтобы олимпиадный каталог не смешивался с основным;
- проверена генерация всех четырёх олимпиадных стартовых модулей через их отдельный каталог.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `Docs/OLYMPIAD_AUTHORING.md`
- `data/templates/olympiad_templates.json`

Проверки:

- компиляция `problemgen/catalog/problem_templates.py` и `problemgen/generation/template_generator.py`;
- генерация модулей `olymp_bignum_add`, `olymp_linear_system_2x2`, `olymp_heads_legs`, `olymp_parity_signed_sum` из отдельного каталога.

Заметки для следующего агента:

- новые олимпиадные задачи добавлять только в отдельный каталог и с префиксом `olymp_`;
- после этого merge все рабочие ветки репозитория входят в `main`.


## 2026-07-15

### Завершение оставшихся строк A04 и демонстрационная генерация

Что сделано:

- все 7 оставшихся OCR-фрагментов листа A04 привязаны к `compare_triple_products_a04_001`, уже проверенному runtime-шаблону сравнения близких произведений;
- ворклист доведён до полного статуса `2121 / 2121 done`;
- добавлена независимая проверка A04: порядок произведений и их разность сравниваются с прямым вычислением на 100 seed;
- подготовлена демонстрационная JSON-выгрузка с реальными сгенерированными задачами.

Измененные файлы:

- `data/source_index/per_task_template_worklist.json`
- `tests/test_template_generator.py`
- `Docs/AGENT_STATUS.md`
- `Docs/FILE_INDEX.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- нет.

Проверки:

- `python3 -m unittest discover -s tests -p 'test_*.py'`;
- A04 проверен прямым вычислением на 100 seed;
- JSON-ворклист проверен через `jq empty` и содержит 0 строк вне `done`.

Заметки для следующего агента:

- исходные формулировки этих 7 строк повреждены OCR, поэтому они используют семейство A04, а не претендуют на буквальную реконструкцию корпуса;
- `Docs/all_tasks_all_files.md` не изменялся.


## 2026-07-15

### Семантическая интеграция authoring-групп A–K и повторная проверка

Что сделано:

- в `main` интегрированы ветки `authoring/A`–`authoring/K`; для общих JSON-файлов использовано объединение по `template_id` и `corpus_id`, чтобы независимые тематические правки не терялись при построчных конфликтах;
- в runtime-каталог внесены авторские шаблоны групп A–K, а ранний набор I из ветки H заменён более полным набором ветки I;
- в генератор добавлены стратегии и formula-helper'ы всех групп; A02 строится от целого ответа и проверяет обратное равенство для точного деления;
- интегрированы исправления русских счётных форм из веток B, E, F, H, I, K;
- добавлены независимые тесты H и расширены проверки каталога для групп C, F, G, I, K;
- claim-board синхронизирован с фактическим состоянием: 2114 из 2121 строк ворклиста имеют `done`.

Измененные файлы:

- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `problemgen/catalog/problem_templates.py`
- `problemgen/generation/template_generator.py`
- `tests/test_template_generator.py`
- `Docs/AGENT_STATUS.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `scripts/replace_group_k_templates.py`
- `tests/test_h_grid_solid_templates.py`

Проверки:

- `python3 -m py_compile problemgen/catalog/problem_templates.py problemgen/generation/template_generator.py scripts/replace_group_k_templates.py tests/test_template_generator.py tests/test_h_grid_solid_templates.py`;
- `python3 -m unittest discover -s tests -p 'test_*.py'` — 78 тестов, OK;
- JSON-каталог и ворклист разобраны через `jq empty`; проверены уникальные ID и наличие стратегий для каталога.

Заметки для следующего агента:

- 7 незавершённых строк находятся только в группе A; не отмечать их `done` без отдельных точных шаблонов и независимой проверки;
- новые числовые стратегии должны, как A02, строить параметры от известного ответа и проверять обратную формулу, если задача требует целого результата;
- `Docs/all_tasks_all_files.md` не изменялся.


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


### Сайт выбора 5 тем и сложностей

Задача:

- сделать сайт, который создает ученический лист с 5 математическими задачами;
- для каждой задачи отдельно выбирать тему и сложность.

Что сделано:

- `problemgen/web/worksheet_site.py` теперь рендерит 5 карточек задач с выбором
  темы и сложности;
- сайт переделан под новое дерево: показывает 100 тем `tree_*`, сгруппированных
  по русским веткам дерева;
- пользователь видит русские названия тем, например
  `A01 · Вычисление длинного выражения`, а технические `module`-идентификаторы
  остаются только в HTML/API;
- `frontend/worksheet_site.js` показывает доступные сложности выбранной темы,
  отключает неподходящие значения и собирает `items` для `POST /generate`;
- `frontend/worksheet_site.css` обновлен под карточный конструктор листа;
- добавлен тест `tests/test_worksheet_site.py`.

Измененные файлы:

- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.js`
- `frontend/worksheet_site.css`
- `Docs/WEB_GENERATION.md`
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

- `tests/test_worksheet_site.py`

Проверки:

- render/API-проверка подтвердила 100 русских тем дерева, 5 выборов темы и 5
  выборов сложности;
- `python -m unittest tests.test_worksheet_site tests.test_template_generator tests.test_worksheet_service` — 17 тестов, OK;
- `python -m unittest discover -s tests` — 34 теста, OK;
- `generate_worksheet_artifacts(...)` успешно создал PDF и два JSON-файла через
  тот же сервис, который вызывает сайт, с пятью темами нового дерева.


## 2026-07-14 — полный корпус `all_tasks_all_files` и one-to-one шаблоны

Задача:

- заменить неверный bridge-подход на конечный детерминированный pipeline;
- прочитать `Docs/all_tasks_all_files.md`;
- создать дерево модулей, rejected-файл, один шаблон на каждую валидную задачу
  и отчеты покрытия.

Что сделано:

- добавлен `problemgen/source_index/all_tasks_pipeline.py`;
- добавлены ручные entry point-скрипты:
  `scripts/build_all_tasks_corpus.py` и `scripts/validate_all_tasks_corpus.py`;
- создано дерево `data/source_index/All_tasks_structure_tree.json`;
- создан one-to-one каталог `data/templates/All_tasks_templates.json`;
- создан `data/source_index/All_tasks_rejected_problems.json`;
- созданы отчеты:
  `data/source_index/All_tasks_modules_summary.md` и
  `data/templates/All_tasks_template_coverage_report.md`;
- также записаны compatibility-копии с точными именами `All_tasks_*` в корень
  проекта;
- добавлен тест `tests/test_all_tasks_pipeline.py`.

Итоговые числа:

- Extracted records: 2121
- Valid problems: 2121
- Rejected records: 0
- Modules: 21
- Templates: 2121
- Problems covered by templates: 2121
- Duplicates: 0
- Missing templates: 0
- Reconstruction tests passed: 2121
- Templates requiring manual or specialized validation: 2121

Заметки для следующего агента:

- `All_tasks_templates.json` является корпусным one-to-one каталогом;
- все шаблоны пока помечены `generation_status: requires_specialized_validator`,
  потому что безопасная рандомизация требует отдельных математических валидаторов;
- старый bridge-слой `tree_*` не должен считаться полноценной заменой
  one-to-one шаблонов из корпуса.

Проверки:

- `python scripts/build_all_tasks_corpus.py` — OK;
- `python scripts/validate_all_tasks_corpus.py` — OK;
- `python -m unittest tests.test_all_tasks_pipeline` — 3 теста, OK;
- `python -m unittest discover -s tests` — 37 тестов, OK.


## 2026-07-15 — очистка `All_tasks_templates.json` до number-only placeholders

Задача:

- переписать существующий каталог шаблонов так, чтобы в `template_text`
  переменными были только числовые значения вида `{number_N}`;
- оставить имена, локации, предметы, единицы, существительные и все обычные
  слова literal text;
- убрать старые `Entity_number_*` placeholders и metadata;
- создать rejected-файл и cleanup report.

Что сделано:

- добавлен `problemgen/source_index/template_cleanup.py`;
- добавлены скрипты:
  `scripts/cleanup_all_tasks_templates.py` и
  `scripts/validate_clean_all_tasks_templates.py`;
- создан очищенный каталог `data/templates/all_tasks_templates.json`;
- создан `data/templates/all_tasks_templates_rejected.json`;
- создан `data/templates/all_tasks_templates_cleanup_report.md`;
- создан `data/templates/all_tasks_templates_cleanup_stats.json`;
- добавлен тест `tests/test_all_tasks_template_cleanup.py`;
- compatibility-копии `all_tasks_templates*` записаны в корень проекта.

Итоговые числа:

- Original templates: 2121
- Retained templates: 2119
- Rejected templates: 2
- Templates repaired: 0
- Templates with only number placeholders: 2119
- Forbidden placeholders remaining: 0
- Control characters remaining: 0
- Reconstruction tests passed: 2119
- Reconstruction tests failed: 0
- Manual-review records: 0

Заметки для следующего агента:

- canonical cleaned catalog: `data/templates/all_tasks_templates.json`;
- исходный one-to-one catalog `data/templates/All_tasks_templates.json` сохранен
  как upstream/source для cleanup;
- cleaned catalog не содержит non-number placeholder metadata.

Проверки:

- `python scripts/cleanup_all_tasks_templates.py` — OK;
- `python scripts/validate_clean_all_tasks_templates.py` — OK;
- `python -m unittest tests.test_all_tasks_template_cleanup` — 3 теста, OK.


## 2026-07-15 — фильтрация `all_tasks_templates.json` по answer definitions

Задача:

- удалить из `all_tasks_templates.json` каждый шаблон без валидного
  `answer_type` и исполнимого/проверяемого `answer_formula`;
- не придумывать формулы и не реконструировать математику;
- сохранить удаленные записи в `all_tasks_templates_rejected.json`.

Что сделано:

- добавлен `problemgen/source_index/answer_definition_cleanup.py`;
- добавлены скрипты:
  `scripts/cleanup_answer_definitions.py` и
  `scripts/validate_answer_definitions.py`;
- создан `data/templates/all_tasks_answer_definition_cleanup_report.md`;
- создан `data/templates/all_tasks_answer_definition_cleanup_stats.json`;
- добавлен тест `tests/test_answer_definition_cleanup.py`.

Итоговые числа:

- Original templates: 2119
- Retained templates: 0
- Newly rejected templates: 2119
- Previously rejected templates: 2
- Total rejected templates: 2121
- Missing answer definitions removed: 2119
- Missing answer types remaining: 0
- Unknown answer types remaining: 0
- Empty answer formulas remaining: 0
- Invalid answer formulas remaining: 0
- Undefined formula variables remaining: 0
- Missing validators remaining: 0
- Answer-type mismatches remaining: 0

Проверки:

- `python scripts/cleanup_answer_definitions.py` — OK;
- `python scripts/validate_answer_definitions.py` — OK;
- `python -m unittest tests.test_answer_definition_cleanup` — 6 тестов, OK;
- `python -m unittest discover -s tests` — 46 тестов, OK.


## 2026-07-15 — восстановление `all_tasks_templates.json`

Задача:

- восстановить шаблоны, удаленные answer-definition cleanup.

Что сделано:

- из `all_tasks_templates_rejected.json` восстановлены все записи с полным
  `original_template`;
- `data/templates/all_tasks_templates.json` снова содержит 2119 шаблонов;
- в `data/templates/all_tasks_templates_rejected.json` оставлены только 2 старые
  rejected-записи, которые были служебными фрагментами, а не задачами;
- обновлены recovery stats/report для answer-definition cleanup.

Проверка:

- `python scripts/validate_clean_all_tasks_templates.py` — OK.


## 2026-07-15 — сайт выбора пяти шаблонов из `all_tasks_templates.json`

Задача:

- создать сайт, который загружает реальные записи из
  `data/templates/all_tasks_templates.json`;
- показывает реальные шаблоны из каталога; шаблоны без формул ответа доступны
  в fallback-режиме с исходными числами;
- дает пять русских selector-полей, предпросмотр листа, ответы и печать.

Что сделано:

- добавлен `problemgen/worksheet/all_tasks_site.py`;
- `problemgen/web/worksheet_site.py` переподключен с дерева тем на
  `all_tasks_templates.json`;
- обновлены `frontend/worksheet_site.js` и `frontend/worksheet_site.css`;
- добавлен `scripts/validate_worksheet_site_catalog.py`;
- обновлены тесты `tests/test_worksheet_site.py`.

Итоговые числа по текущему каталогу:

- Total templates in catalog: 2119
- Templates eligible for selection: 2119
- Templates excluded from selection: 0
- Templates excluded for forbidden placeholders: 0
- Templates excluded for invalid formulas: 0
- Templates excluded for unsupported answer types: 0
- Templates excluded for missing safe generators: 0
- Selectable templates without answer formula: 2119
- Selectable templates passing fallback rendering tests: 2119

Причина:

- все восстановленные шаблоны сейчас имеют `answer_type: "unknown"` и пустой
  `answer_formula`, поэтому сайт не выдумывает ответы и использует исходные
  `original_values` как preview/fallback до добавления настоящих формул.

Проверки:

- `python scripts/validate_worksheet_site_catalog.py` — OK;
- `python -m unittest tests.test_worksheet_site` — 6 тестов, OK;
- `python -m unittest discover -s tests` — 50 тестов, OK.


## 2026-07-15 — очистка текстов `all_tasks_templates.json`

Задача:

- убрать из активного каталога OCR-мусор, лишнюю source-нумерацию,
  бессмысленные хвосты и обрезанные условия;
- чинить только безопасные и high-confidence случаи;
- нереконструируемые фрагменты переносить в `all_tasks_templates_rejected.json`.

Что сделано:

- добавлен `problemgen/source_index/text_quality_cleanup.py`;
- добавлены скрипты:
  `scripts/cleanup_all_tasks_template_texts.py` и
  `scripts/validate_all_tasks_template_texts.py`;
- создан `data/templates/all_tasks_templates_text_cleanup_report.md`;
- создан `data/templates/all_tasks_templates_text_cleanup_stats.json`;
- добавлены тесты `tests/test_template_text_cleanup.py`;
- активный сайт теперь видит только cleaned active catalog.

Итоговые числа:

- Original active templates: 2119
- Repaired templates: 28
- Newly rejected templates: 1031
- Final active templates: 1088
- Redundant numbering prefixes remaining: 0
- Meaningless OCR fragments remaining: 0
- Forbidden control characters remaining: 0
- Incomplete templates remaining: 0
- Templates failing reconstruction/text lint: 0
- Templates failing answer validation: 1088
- Templates failing generated-text tests: 0
- Manual-review templates: 277

Важно:

- формулы ответов пока не восстановлены: 1088 активных шаблонов всё еще имеют
  `answer_type: "unknown"` или пустой `answer_formula`;
- сайт продолжает показывать эти шаблоны в fallback-режиме с исходными числами
  и не выдумывает ответы.

Проверки:

- `python scripts/cleanup_all_tasks_template_texts.py` — OK;
- `python scripts/validate_all_tasks_template_texts.py` — OK;
- `python scripts/validate_worksheet_site_catalog.py` — OK;
- `python -m unittest tests.test_template_text_cleanup` — 7 тестов, OK;
- `python -m unittest discover -s tests` — 59 тестов, OK.
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


## 2026-07-15

### Реестр занятости ветки authoring/D

Задача:

- сделать видимым, что группа D закреплена за активной веткой до окончания авторинга.

Что сделано:

- добавлен `Docs/BRANCH_ACTIVITY.md` с правилами статусов и записью `authoring/D`;
- ветка отмечена как «в работе», с областью только `D01`–`D09` и 0/9 завершённых листьев;
- в `Docs/FILE_INDEX.md` и `Docs/VECTOR_TREE.md` добавлены назначение и маршрут к реестру.

Измененные файлы:

- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`

Новые файлы:

- `Docs/BRANCH_ACTIVITY.md`

Проверки:

- вручную проверены чистота рабочей ветки перед началом и корректность статуса `authoring/D`.

Заметки для следующего агента:

- не брать листья D и не менять bridge-заглушки `D01`–`D09`, пока запись имеет статус «в работе»;
- после полного завершения группы и открытия PR автор должен сменить статус на «свободна для перепроверки».


### Авторский батч D01: кратные в промежутке

Что сделано:

- добавлена стратегия `d01_multiples_interval` и два авторских шаблона: подсчёт кратных на включающем отрезке и подсчёт кратных одному числу без кратных другому на строгом промежутке;
- все 9 bridge-заглушек `D01` удалены, 19 строк листа в ворклисте получили ссылку на основной runtime-шаблон и статус `done`;
- добавлен `scripts/replace_bridge_leaf.py`: он атомарно заменяет bridge-записи одного leaf и синхронизирует его поля ворклиста.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/FILE_INDEX.md`
- `Docs/WORK_LOG.md`
- `scripts/README.md`

Новые файлы:

- `scripts/replace_bridge_leaf.py`

Проверки:

- независимо пересчитаны четыре сгенерированные задачи D01 простым перебором целых чисел; ответы совпали;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01: 19/19 строк `done`; по группе D остаются D02–D09, 111 задач;
- `replace_bridge_leaf.py` принимает payload со списком шаблонов через stdin и не затрагивает другие листья.


### Авторский батч D02: признаки делимости и пропущенная цифра

Что сделано:

- добавлена стратегия `d02_missing_digit` и безопасная функция `d02_digits_for_mod3`;
- все 9 bridge-заглушек D02 заменены двумя авторскими шаблонами: единственная цифра для делимости на 9 и полный список цифр для делимости на 3;
- второй вариант вынесен в отдельный runtime-модуль `divisibility_missing_residue_multi`, так как один модуль не может одновременно выдавать ответы типов `number` и `multi`;
- 10 строк D02 в ворклисте отмечены `done`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- независимо перебраны цифры 0–9 в четырёх сгенерированных записях; ответы совпали;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01–D02: 29/29 строк `done`; по группе D остаются D03–D09, 101 задача;
- не смешивать в одном `module` шаблоны с разными `answer_type`: общий тест генерирует по модулю.


### Авторский батч D03: минимальная сумма сомножителей

Что сделано:

- добавлена стратегия `d03_factor_pair` и безопасная функция `d03_min_factor_sum`, перебирающая пары делителей до квадратного корня;
- все 9 bridge-заглушек D03 заменены тремя авторскими ограничениями: ровно один нечётный множитель, оба множителя чётные и один нетривиальный квадрат;
- 21 строка D03 в ворклисте получила основной runtime-шаблон и статус `done`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- для пяти сгенерированных задач независимо перебраны все допустимые пары делителей; минимум суммы совпал;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01–D03: 50/50 строк `done`; по группе D остаются D04–D09, 80 задач;
- функция `d03_min_factor_sum` принимает только явные условия `any`, `one_odd`, `both_even`, `one_square` и отклоняет отсутствие подходящей пары.


### Авторский батч D04: разложения с ограничениями на сомножители

Что сделано:

- добавлены стратегия `d04_constrained_factorization` и безопасные функции поиска минимальной пары без цифры 0 и подсчёта ограниченных пар;
- все 9 bridge-заглушек D04 заменены двумя авторскими шаблонами: минимальная сумма сомножителей без нулей в записи и число пар в заданных границах;
- 29 строк D04 в ворклисте отмечены `done`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- для четырёх сгенерированных задач независимо перебраны все пары делителей с ограничениями; ответы совпали;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01–D04: 79/79 строк `done`; по группе D остаются D05–D09, 51 задача;
- `d04_min_nozero_factor_sum` возвращает −1 в случае невозможности, хотя стратегия целенаправленно создаёт хотя бы одну допустимую пару.


### Авторский батч D05: простые числа как параметры

Что сделано:

- добавлена стратегия `d05_prime_parameter`, предикат простоты и безопасные функции поиска наибольшего простого и подсчёта простых;
- все 9 bridge-заглушек D05 заменены двумя авторскими шаблонами на поиск и подсчёт простых чисел;
- единственная строка D05 в ворклисте отмечена `done`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- для четырёх сгенерированных задач простота проверена независимым делением до квадратного корня; ответы совпали;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01–D05: 80/80 строк `done`; по группе D остаются D06–D09, 50 задач;
- функции D05 ограничены числом 990, поэтому линейная проверка простоты остаётся быстрой и предсказуемой.


### Авторский батч D06: НОД, НОК и совпадение периодов

Что сделано:

- добавлена стратегия `d06_gcd_lcm_periods` и два авторских шаблона: разбиение на максимальное число одинаковых групп (НОД) и первое совпадение периодов (НОК);
- все 9 bridge-заглушек D06 удалены, 17 строк листа в ворклисте отмечены `done`;
- страж хрупкости обнаружил несогласованную верхнюю границу 140 на сложности 10; границы `first` и `second` исправлены на 210 по фактическому контракту стратегии.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- НОД и НОК четырёх сгенерированных пар независимо рассчитаны средствами стандартной библиотеки; ответы совпали;
- `python3 -m unittest discover -s tests` — 42 теста, OK после исправления границ.

Заметки для следующего агента:

- D01–D06: 97/97 строк `done`; по группе D остаются D07–D09, 33 задачи;
- верхние границы constraints надо выводить из максимума стратегии на сложности 10, а не из типичных значений.


### Авторский батч D07: остатки и циклы по модулю

Что сделано:

- добавлена стратегия `d07_modular_power_cycle` и функция `d07_pow_mod`, не строящая огромное число степени;
- все 9 bridge-заглушек D07 заменены двумя авторскими шаблонами: остаток большой степени и её последняя цифра;
- 8 строк D07 в ворклисте отмечены `done`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- ответы четырёх задач независимо получены повторным умножением по модулю; результаты совпали;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01–D07: 105/105 строк `done`; по группе D остаются D08–D09, 25 задач;
- `d07_pow_mod` — единственный разрешённый путь для больших показателей, поскольку обычная степень в формулах ограничена 64.


### Авторский батч D08: завершающие нули и показатели простых

Что сделано:

- добавлены стратегия `d08_trailing_zeros` и функции подсчёта завершающих нулей в последовательном произведении и факториале;
- все 9 bridge-заглушек D08 заменены двумя авторскими шаблонами: произведение подряд идущих чисел и факториал;
- 6 строк D08 в ворклисте отмечены `done`;
- до коммита исправлена визуальная формулировка первого шаблона: вместо пустого искусственного плейсхолдера используется неизменяемая запись `({start} + 1)`.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- нули в четырёх сгенерированных задачах независимо подсчитаны по фактическим большим произведениям; ответы совпали;
- вручную подтверждено отсутствие пустых подстановок в отрендеренном тексте;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- D01–D08: 111/111 строк `done`; по группе D остаётся D09, 19 задач;
- не использовать derived_words как средство вычисления чисел: плейсхолдеры в тексте должны либо приходить из стратегии, либо быть буквальной математической записью.


### Авторский батч D09: конструкции по чётности и делимости

Что сделано:

- добавлена стратегия `d09_parity_construction`, функции ответа для инварианта чётности и отбора чисел с простыми множителями только 2 и 3;
- все 9 bridge-заглушек D09 заменены двумя авторскими шаблонами: существование числовой таблицы и поиск «хороших» чисел;
- 19 строк D09 в ворклисте отмечены `done`; авторинг всех девяти листьев группы D завершён.

Измененные файлы:

- `problemgen/generation/template_generator.py`
- `data/templates/problem_templates.json`
- `data/source_index/per_task_template_worklist.json`
- `Docs/BRANCH_ACTIVITY.md`
- `Docs/WORK_LOG.md`

Проверки:

- четыре сгенерированные задачи D09 независимо сверены по чётности числа столбцов и разложению кандидатов на простые множители;
- `python3 -m unittest discover -s tests` — 42 теста, OK.

Заметки для следующего агента:

- все 9 листьев D закрыты: 130/130 строк `done`; передавать ветку на PR и затем менять её статус в `Docs/BRANCH_ACTIVITY.md` на «свободна для перепроверки»;
- `parity_divisibility_construction` и `parity_divisibility_construction_multi` разделены из-за разных типов ответа (`text` и `multi`).


### Доска занятости агентов (claim-board)

Задача:

- исключить, что два агента возьмут одну группу; сделать явный протокол «занял ветку → освободил».

Что сделано:

- добавлен `Docs/AGENT_STATUS.md` — доска со статусами всех 11 групп (`свободна` / `в работе` / `готово (только перепроверка)` / `частично — свободна`), ветка, дата, кто и заметки;
- прописан протокол: claim (пометить `в работе` маленьким коммитом в main до старта) → работа на `authoring/<группа>` → release (`готово` после вливания PR); прерывание возвращает группу в пул;
- `Docs/AGENT_TASKS.md`: добавлена секция «Доска занятости», а промпт агента расширен шагами CLAIM/RELEASE и требованием после своей группы брать следующую свободную, пока есть ресурсы (цель — все группы, не одна);
- отражено стартовое состояние: A и C — `частично — свободна` (сделаны A04, C04), остальные `свободна`.

Измененные файлы:

- `Docs/AGENT_TASKS.md`, `Docs/FILE_INDEX.md`, `Docs/WORK_LOG.md`

Новые файлы:

- `Docs/AGENT_STATUS.md`

Проверки:

- изменения только документационные; тестовый набор не затронут.

Заметки для следующего агента:

- перед стартом обязательно claim в `AGENT_STATUS.md`; это единственная разрешённая прямая правка `main`, вся остальная работа — через PR из `authoring/<группа>`.


### Сверка статуса authoring/D с project claim-board

Что сделано:

- удалён временный `Docs/BRANCH_ACTIVITY.md`, созданный до появления проектной доски;
- статус D и счётчик 130/130 перенесены в единственный источник правды — `Docs/AGENT_STATUS.md`;
- навигация в `Docs/FILE_INDEX.md` и `Docs/VECTOR_TREE.md` приведена к claim-board.

Измененные файлы:

- `Docs/AGENT_STATUS.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Удаленные файлы:

- `Docs/BRANCH_ACTIVITY.md`

Заметки для следующего агента:

- после merge PR ветки `authoring/D` выполнить release по протоколу в `Docs/AGENT_STATUS.md`: `готово (только перепроверка)`;
- до merge не освобождать D: иначе параллельный автор может начать менять уже готовую, но ещё не влитую работу.


### Импорт сборника задач для подготовки к 239

Задача:

- добавить в репозиторий переданный пользователем исходный сборник и явно указать его связь с существующим корпусом.

Что сделано:

- исходный UTF-8 файл скопирован без изменений в `Docs/source_documents/Сборник задач по подготовке к 239 в 5 класс.txt`;
- создан `Docs/source_documents/README.md` с контрактом read-only импорта и SHA-256;
- `Docs/all_tasks_all_files.md` не менялся: по архитектурному контракту это существующий неизменяемый master-корпус;
- обновлены документация и маршруты к новому источнику.

Измененные файлы:

- `Docs/README.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `Docs/source_documents/README.md`
- `Docs/source_documents/Сборник задач по подготовке к 239 в 5 класс.txt`

Проверки:

- `cmp` подтвердил побайтовое совпадение с файлом из `/Users/a01/Downloads/`;
- SHA-256 обеих копий: `e22c567cdfca9b3dc3894919257f2b29c415d078e3ebef79838eaf2400d350cc`.

Заметки для следующего агента:

- если задачи из этого сборника понадобятся генератору, сначала создать отдельную разметку/дедупликацию в `data/source_index/`, не изменяя `Docs/all_tasks_all_files.md`.


### Верификация Группы D и брифы/промпты по группам

Задача:

- проверить работу параллельного агента (Группа D) и подготовить per-group промпты с предметными комментариями.

Что сделано:

- независимо (brute-force, 20–200 сидов на тип) сверены ответы Группы D: D01, D02, D04, D05 (два парных шаблона), D06 (=НОК), D07/D08 (helper'ы), D09 — 0 реальных ошибок; первичная тревога «49 несовпадений» оказалась дефектом харнесса (варианты формулировок), а не шаблонов; заглушек `tree_d` не осталось, 19 авторских D-шаблонов, тесты 42 OK;
- добавлен `Docs/AGENT_GROUP_BRIEFS.md`: по каждой из групп B/E/F/G/H/I/J/K — тип математики, какие функции движка добавить, как сверять ответы, подводные камни и сложность; закреплены два правила (отдельный worktree на агента; независимая сверка ответа, не только тип);
- в `AGENT_TASKS.md` правило про ветку усилено до обязательного worktree.

Измененные файлы:

- `Docs/AGENT_TASKS.md`, `Docs/FILE_INDEX.md`, `Docs/WORK_LOG.md`

Новые файлы:

- `Docs/AGENT_GROUP_BRIEFS.md`

Проверки:

- brute-force сверка D — 0 ошибок; `python -m unittest discover -s tests` — 42 OK.

Заметки для следующего агента:

- сложные группы: H (перегородки в фигурах с вырезами), I (нужны календарные функции), K (логические solver'ы) — брать простые листья первыми, тяжёлые помечать в notes;
- обязательно отдельный worktree; сверять ответ независимым расчётом.


### Арифметические шаблоны по `01_arifmeticheskie_vychisleniya_updated.md`

Дата: 2026-07-15

Задача:

- создать параметрический каталог, генератор, сайтовый выбор пяти шаблонов и проверки для модуля арифметических вычислений.

Что сделано:

- добавлен `data/templates/problem_sets/arithmetic/templates.json` с 39 уникальными структурами, которые покрывают все 75 исходных номеров ровно один раз;
- добавлен `problemgen/generation/arithmetic_templates.py` с загрузкой, валидацией, генерацией по seed, расчетом ответов и сборкой листа из пяти задач;
- `problemgen/web/worksheet_site.py` переключен на новый арифметический каталог, а HTML-лист сохраняет существующие `assets/logo.png` и `assets/qr.png`;
- добавлены `scripts/validate_arithmetic_templates.py` и `scripts/generate_arithmetic_worksheet.py`;
- добавлены тесты `tests/test_arithmetic_templates.py`;
- добавлена документация `docs/arithmetic_templates.md`.

Измененные файлы:

- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.js`
- `frontend/worksheet_site.css`
- `scripts/README.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `data/templates/problem_sets/arithmetic/templates.json`
- `problemgen/generation/arithmetic_templates.py`
- `scripts/validate_arithmetic_templates.py`
- `scripts/generate_arithmetic_worksheet.py`
- `tests/test_arithmetic_templates.py`
- `docs/arithmetic_templates.md`

Проверки:

- `python scripts/validate_arithmetic_templates.py` — OK: 33 templates, 75 source problem numbers, 100 seeds each;
- `python -m unittest tests.test_arithmetic_templates` — OK, 8 tests;
- `python scripts/generate_arithmetic_worksheet.py --seed 12345` — создан `outputs/generated/arithmetic_worksheet_example.json`, 5 задач;
- ручная проверка сайта на `127.0.0.1:8094`: `/api/templates` вернул 33 шаблона, `/generate` вернул `ok=True` и 5 задач;
- `python -m unittest discover -s tests` — OK, 82 tests.

Дополнительная сверка логики после ревью пользователя:

- исправлен шаблон `arithmetic_007`: первый шаг строго `+1`, затем только растущие четные приращения;
- `arithmetic_014` закреплен как прогрессия с шагом 3;
- одночастные и многочастные исходные задачи разделены на отдельные шаблоны (`1123/1323`, `1522`, `1233/1433`, `1231/1431`, `1523`, `1101`);
- `python scripts/validate_arithmetic_templates.py` — OK: 39 templates, 75 source problem numbers, 100 seeds each;
- `python -m unittest tests.test_arithmetic_templates` — OK, 11 tests.


### Реорганизация шаблонов в problem sets

Дата: 2026-07-15

Задача:

- подготовить структуру, куда можно складывать похожие файлы с другими разделами задач, не ломая сайт арифметического генератора.

Что сделано:

- `data/templates/arithmetic_templates.json` перенесен в `data/templates/problem_sets/arithmetic/templates.json`;
- добавлен общий каталог `data/templates/problem_sets/catalog.json`;
- добавлены README-файлы для `data/templates/problem_sets/` и `data/templates/problem_sets/arithmetic/`;
- `problemgen/generation/arithmetic_templates.py` теперь по умолчанию читает новый путь, но сохраняет fallback на старый путь;
- сайт продолжает работать с арифметическим набором.

Измененные файлы:

- `problemgen/generation/arithmetic_templates.py`
- `problemgen/web/worksheet_site.py`
- `docs/arithmetic_templates.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`
- `scripts/README.md`

Новые файлы:

- `data/templates/problem_sets/README.md`
- `data/templates/problem_sets/catalog.json`
- `data/templates/problem_sets/arithmetic/README.md`
- `data/templates/problem_sets/arithmetic/templates.json`

Проверки:

- `python scripts/validate_arithmetic_templates.py` — OK: 39 templates, 75 source problem numbers, 100 seeds each;
- `python -m unittest tests.test_arithmetic_templates` — OK, 11 tests.


### Сайт выбирает модули, а не отдельные шаблоны

Дата: 2026-07-15

Задача:

- сделать так, чтобы пользователь выбирал модуль задач в каждом слоте листа, а конкретный шаблон выбирался случайно внутри модуля.

Что сделано:

- `/api/templates` теперь дополнительно отдает список `modules`;
- сайт показывает один доступный модуль `arithmetic`, а не 39 отдельных шаблонов;
- один и тот же модуль можно выбрать в нескольких слотах, включая все пять;
- `POST /generate` принимает `module_ids` и генерирует по одному случайному шаблону из модуля на каждый слот;
- старый режим `template_ids` оставлен в backend для совместимости.

Измененные файлы:

- `problemgen/generation/arithmetic_templates.py`
- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.js`
- `tests/test_arithmetic_templates.py`
- `docs/arithmetic_templates.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Проверки:

- `python -m unittest tests.test_arithmetic_templates` — OK, 13 tests;
- site smoke test: `/api/templates` вернул `modules=1`, первый модуль `arithmetic`;
- site smoke test: `POST /generate` с пятью `module_ids=["arithmetic", ...]` вернул `ok=True`, 5 задач, `modules_used=arithmetic`.


### Печать, быстрый вариант и локальный Lato

Дата: 2026-07-15

Задача:

- сделать начальный вариант в одну кнопку с автоматически выбранными модулями;
- позволить менять число задач и исправить печать с отдельной отрезаемой
  колонкой ответов;
- заменить системные шрифты на локальную кириллическую Lato.

Что сделано:

- `problemgen/web/worksheet_site.py` теперь принимает от 1 до 20 задач,
  поддерживает `mode: "random"` и собирает быстрый вариант только из 215
  шаблонов с вычисляемыми ответами;
- добавлен ручной архивный модуль из 1088 очищенных записей
  `data/templates/all_tasks_templates.json`; архив не попадает в быстрый
  вариант и явно не выдаёт выдуманный ответ, пока формулы не восстановлены;
- `frontend/worksheet_site.js` строит число селекторов по полю количества
  задач, запускает «деревянный вариант» и дублирует ответы в печатную колонку;
- `frontend/worksheet_site.css` печатает A4 в landscape, добавляет пунктирную
  линию отреза и подключает локальную Lato;
- добавлены `assets/fonts/Lato-Regular.ttf`, `Lato-Bold.ttf`,
  `Lato-Black.ttf` и лицензия `assets/fonts/OFL.txt` из официального набора
  Lato OFL;
- актуализированы `Docs/WEB_GENERATION.md`, `Docs/FILE_INDEX.md` и
  `Docs/VECTOR_TREE.md`.

Изменённые файлы:

- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.js`
- `frontend/worksheet_site.css`
- `tests/test_worksheet_site.py`
- `assets/README.md`
- `Docs/WEB_GENERATION.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `assets/fonts/Lato-Regular.ttf`
- `assets/fonts/Lato-Bold.ttf`
- `assets/fonts/Lato-Black.ttf`
- `assets/fonts/OFL.txt`
- `assets/fonts/README.md`

Проверки:

- `python3 -m py_compile problemgen/web/worksheet_site.py` — OK;
- `node --check frontend/worksheet_site.js` — OK;
- fixed-seed генерация 1, 5 и 8 задач — OK; быстрый вариант содержит только
  проверяемые ответы;
- проверка archive-модуля подтверждает, что вместо выдуманного ответа выводится
  явный статус отсутствующей формулы.
- браузерный прогон `http://127.0.0.1:8090`: быстрый вариант успешно создал 5
  и затем 7 задач, столько же ответов появилось в отрезаемой печатной колонке;
  UI и локальная Lato визуально проверены.
- `python3 -m unittest discover -s tests -p 'test_*.py'` — 125 тестов, 8
  исторических падений в несвязанном контуре `problem_templates.json`: тесты
  ожидают 1528 записей, а его активный runtime-каталог содержит 184. Новая
  функциональность этого листа к ним не относится.


### Визуальный шаблон «Поступление в 239»

Дата: 2026-07-15

Задача:

- привести интерфейс и распечатанный лист к предоставленным визуальным
  референсам: сине-белая посадочная страница и строгий вертикальный лист.

Что сделано:

- добавлен предоставленный пользователем знак `assets/logo_239.png`;
- `problemgen/web/worksheet_site.py` выводит компактную фирменную навигацию и
  использует знак в листе и в отрезаемой колонке;
- `frontend/worksheet_site.css` заменён с деревянной темы на сине-белую,
  близкую к референсу; печатный формат переключён на A4 portrait;
- учебный лист оформлен по образцу: верхняя линия, поля «Фамилия», «Имя»,
  «Дата», разделители между задачами, знак и QR справа;
- для печати с ответами знак, QR и ответы размещаются в отдельной правой
  пунктирной полосе.

Изменённые файлы:

- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.css`
- `Docs/WEB_GENERATION.md`
- `Docs/FILE_INDEX.md`
- `Docs/VECTOR_TREE.md`
- `Docs/WORK_LOG.md`

Новые файлы:

- `assets/logo_239.png`

Проверки:

- `python3 -m py_compile problemgen/web/worksheet_site.py` — OK;
- `node --check frontend/worksheet_site.js` — OK;
- `python3 -m unittest tests.test_worksheet_site tests.test_arithmetic_templates
  tests.test_equation_templates tests.test_system_equation_templates
  tests.test_comparison_templates` — 49 тестов, OK;
- ручная проверка в локальном браузере: кнопка готового варианта создаёт 5
  заданий и 5 ответов в правой отрезаемой полосе; фирменный знак доступен.
