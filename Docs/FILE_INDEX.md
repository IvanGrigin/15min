# Индекс файлов

## Модуль 10: отношения, доли, пропорции и проценты

- `docs/10_otnosheniya_doli_proportsii_i_protsenty_bez_imen_i_personazhey_deduplicated.md` и `docs/10_otnosheniya_doli_proportsii_i_protsenty_s_imenami_i_personazhami_deduplicated.md` — read-only корпус 12 и 14 уникальных задач; используется только для source accounting и выделения математических типов.
- `data/templates/problem_sets/ratios_fractions_proportions_and_percentages/templates.json` — 12 активных semantic-шаблонов с целым ответом; загружается `problemgen/generation/ratio_templates.py`.
- `data/templates/problem_sets/ratios_fractions_proportions_and_percentages/source_accounting.json` — one-to-one учёт 26 источников: active template либо точная причина исключения.
- `data/templates/problem_sets/ratios_fractions_proportions_and_percentages/README.md` — назначение набора и короткие команды проверки.
- `problemgen/generation/ratio_templates.py` — каталог, стратегии, независимые решатели, approved-character binding и metadata для сайта.
- `scripts/validate_ratio_templates.py` — ручной прогон 12 шаблонов по 200 seed.
- `tests/test_ratio_templates.py` — source/schema/math/grammar/site регрессия модуля.
- `Docs/ratio_templates.md` — русский контракт, семейства, исключения и инструкция расширения.

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


### `Docs/KNOWLEDGE_BASE.md`

Назначение:

- контракт базы знаний агентов (TriliumNext Trilium, локальный инстанс);
- обязательная иерархия, workflow git-зеркала `knowledge/`, правила и запреты;
- используется вместе с `scripts/kb_server.mjs` и `scripts/kb.mjs`.


### `Docs/AGENT_KB_BOOTSTRAP.md`

Назначение:

- самодостаточная инструкция и промт для внедрения такой же базы знаний в
  другом проекте;
- не зависит от содержимого этого репозитория.


### `Docs/all_tasks_all_files.md`

Назначение:

- основной read-only корпус примеров и типов задач.

Правило:

- не редактировать.


### `Docs/source_documents/`

Назначение:

- хранит неизменённые пользовательские источники, добавленные после построения основного корпуса;
- не заменяет и не переписывает `Docs/all_tasks_all_files.md`;
- передаёт документы следующему этапу — отдельной разметке в `data/source_index/`.

Ключевые файлы и связи:

- `README.md` — контракт read-only импорта и контрольная сумма текущего файла;
- `Сборник задач по подготовке к 239 в 5 класс.txt` — исходный сборник задач; его будущим потребителем будет отдельный индекс в `data/source_index/`.


## Папка `data/`

### `assets/README.md`

Назначение:

- описание дефолтных изображений и локальных шрифтов для листов;
- объясняет, как заменить логотип, QR-код и откуда берётся Lato без правки
  Python-кода.


### `assets/fonts/`

Назначение:

- самодостаточные кириллические файлы Lato Regular, Bold и Black;
- `OFL.txt` фиксирует лицензию шрифта;
- `README.md` фиксирует источник, лицензию и web-подключение;
- используются `frontend/worksheet_site.css` и HTTP-обработчиком
  `problemgen/web/worksheet_site.py`.


### `assets/logo.png`

Назначение:

- дефолтный логотип для правой панели ученического листа.


### `assets/qr.png`

Назначение:

- QR-код `https://t.me/postuplenie239` с белой тихой зоной для шапки
  ученического листа и отрезаемой колонки ответов.


### `assets/logo_239.png`

Назначение:

- предоставленный пользователем знак «Поступление в 239»;
- используется как фирменный знак в web-интерфейсе и рядом с QR-кодом в
  распечатанном варианте.

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


### `data/source_index/all_tasks_tree_by_theme_and_difficulty.md`

Назначение:

- короткий указатель на новую раздельную структуру `data/source_index/task_tree/`;
- сохранен для обратной совместимости со старыми ссылками.


### `data/source_index/math_problem_tree_template_ready.md`

Назначение:

- короткий указатель на production-планирование, перенесенное в листья `data/source_index/task_tree/`;
- сохранен для обратной совместимости со старыми ссылками.


### `data/source_index/task_tree/`

Назначение:

- компактная тематическая навигация по 2 121 нумерованным записям read-only корпуса;
- содержит корневой `README.md`, 11 индексов разделов, 100 файлов-листьев и `manifest.json`;
- каждый лист объединяет таксономию, план будущего шаблона и записи корпуса, но не заявляет наличие runtime-шаблона;
- используется агентами и разработчиками, которым нужно открыть только одну тему без загрузки больших обзорных документов.


### `data/source_index/per_task_template_worklist.json`

Назначение:

- ворклист с одним слотом на каждую из 2121 задач корпуса под будущий точный шаблон и формулу ответа;
- сводит текст задачи с темой/сложностью из `task_tree`; поля `template_text`/`number_strategy`/`answer_formula` заполняются вручную;
- генерируется скриптом `scripts/build_per_task_template_worklist.py`, идемпотентно.
- после завершения A04 содержит 2121 строку со статусом `done`; OCR-фрагменты A04 связаны с общим проверенным шаблоном сравнения произведений.


### `Docs/TEMPLATE_AUTHORING_GUIDE.md`

Назначение:

- полное руководство по написанию шаблонов: анатомия, возможности движка, правила стратегий, цикл замены заглушки, Definition of Done.
- фиксирует выбор из трёх изолированных путей: production-каталог, архивный
  recovery-overlay или олимпиадный каталог; для recovery задаёт обязательную
  проверку исходного ответа, связанных параметров и случайных seed.


### `Docs/AGENT_TASKS.md`

Назначение:

- разбивка работы по замене 900 заглушек на 11 групп тем (по агенту на группу), правила координации и готовый промпт для запуска агента.
- требует одну существующую рабочую папку, отдельную ветку на задачу и merge в
  `main` через PR; создание worktree и временных копий запрещено.


### `Docs/AGENT_STATUS.md`

Назначение:

- доска занятости: какая группа сейчас `в работе`, какая `свободна`, какая `готово`;
- протокол claim/release, чтобы два агента не взяли одну группу.


### `Docs/AGENT_GROUP_BRIEFS.md`

Назначение:

- per-group промпты и предметные комментарии (математика, нужные функции движка, сверка ответов, подводные камни) для всех 11 групп;
- фиксирует два правила: отдельная ветка без новой рабочей папки и независимая
  проверка ответов.


### `data/templates/README.md`

Назначение:

- описание каталога формализованных шаблонов.


### `data/templates/worksheets/README.md`

Назначение:

- описание JSON-шаблонов листов с задачами;
- фиксирует, что здесь лежит только визуальная раскладка.


### `data/templates/worksheets/worksheet_5_tasks.json`

Назначение:

- готовый JSON-шаблон листа с 5 задачами;
- задает координаты полей, слотов, линий и правой панели.


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


### `data/language/nouns/russian_nouns.json`

Назначение:

- библиотека 100+ русских существительных с полными парадигмами (12 форм каждое);
- загружается в Python через `problemgen/russian/noun_dict.py`;
- пополняется без изменения Python-кода — достаточно добавить запись в JSON.


### `data/language/nouns/README.md`

Назначение:

- инструкция по добавлению новых слов в `russian_nouns.json`;
- описание всех полей (gender, animate, legs, tags, count_forms, forms).


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


### `problemgen/io/worksheet_renderer.py`

Назначение:

- загружает JSON-шаблон листа;
- читает задачи из bundle-формата и простого списка;
- проверяет число задач, переносит текст по строкам и рендерит итог в `PDF` или `PNG`.

Ключевые сущности:

- `WorksheetRenderError`
- `load_worksheet_template(...)`
- `load_problem_texts(...)`
- `build_worksheet_plan(...)`
- `render_worksheet(...)`


## Папка `problemgen/worksheet/`

### `problemgen/worksheet/README.md`

Назначение:

- описание orchestration-слоя генерации ученических листов.


### `problemgen/worksheet/all_tasks_site.py`

Назначение:

- безопасно рендерит очищенные архивные шаблоны;
- накладывает только явные проверенные формулы из
  `data/templates/all_tasks_answer_recovery.json`;
- разделяет восстановленные задачи с ответами и неразобранные записи без
  выдуманного ответа;
- хранит стратегии генерации для связанных архивных параметров, включая
  календарные майские даты и задачи на длительность событий в разных часовых
  поясах.

Ключевые сущности:

- `catalog_with_recovered_answers(...)`;
- `recovered_templates()`;
- `unverified_templates()`;
- `_generate_cube_subdivision_values(...)`;
- `_generate_centered_rectangle_hole_values(...)`;
- `_generate_two_square_holes_values(...)`;
- `_generate_elimination_tournament_values(...)`;
- `_generate_divisibility_interval_values(...)`;
- `_generate_even_divisibility_interval_values(...)`;
- `_generate_odd_strict_interval_values(...)`;
- `_generate_language_overlap_values(...)`;
- `_generate_roundtrip_distance_values(...)`;
- `_generate_square_grid_values(...)`;
- `_generate_gnomes_and_ponies_values(...)`;
- `_generate_birthday_food_values(...)`;
- `_generate_timezone_olympiad_values(...)`;
- `_generate_may_day_of_month_values(...)`;
- `_generate_may_sunday_noon_hours_values(...)`;
- `_generate_gulliver_chase_values(...)`;
- `_generate_backward_tower_clock_values(...)`;
- `_generate_oleg_away_time_values(...)`;
- `generate_problem_instance(...)`.


### `problemgen/worksheet/service.py`

Назначение:

- принимает 5 уровней сложности от 1 до 10;
- генерирует 5 задач через существующие арифметические шаблоны;
- сохраняет student JSON и answers JSON;
- вызывает рендер листа и возвращает пути к итоговым артефактам.

Ключевые сущности:

- `WorksheetProblem`
- `WorksheetArtifact`
- `validate_difficulties(...)`
- `map_numeric_difficulty_to_level(...)`
- `generate_worksheet_artifacts(...)`


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


### `problemgen/russian/inflection.py`

Назначение:

- структура `RussianNoun` с 12 явными падежными формами;
- поддержка `count_one/few/many` для нестандартных парадигм (год→лет, человек, мороженое).


### `problemgen/russian/noun_dict.py`

Назначение:

- загружает NOUNS из `data/language/nouns/russian_nouns.json`;
- экспортирует `NOUNS`, `get_noun()`.


### `problemgen/russian/template_engine.py`

Назначение:

- `render_template(template, context)` — движок подстановки слотов;
- синтаксис: `{key}`, `{key:case}`, `{key:count,numkey}`, `{key:agree,numkey}`.


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


### `problemgen/web/worksheet_site.py`

Назначение:

- локальный HTTP-сайт для листов с 1–20 задачами;
- объединяет проверяемые problem sets и отдельно помеченный архив очищенных
  текстовых шаблонов;
- принимает быстрый `mode: random` и ручной `module_ids` в `POST /generate`;
- безопасно отдаёт локальные файлы Lato для печати.


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


### `frontend/worksheet_site.css`

Назначение:

- подключает локальный Lato, сине-белую тему по фирменному референсу и
  печатный режим A4 landscape с увеличенным полем для решения после задачи,
  компактной раскладкой пяти задач на одном листе и пунктирной отрезаемой
  колонкой ответов.


### `frontend/worksheet_site.js`

Назначение:

- регулирует количество задач, строит ручные выборщики модулей и запускает
  быстрый случайный вариант;
- отправляет `POST /generate`, показывает ответы на экране и заполняет
  отдельную печатную колонку ответов.


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


### `scripts/render_worksheet.py`

Назначение:

- ручной запуск рендера листа с задачами по JSON-шаблону.


### `scripts/generate_worksheet.py`

Назначение:

- генерация ученического листа по 5 числовым уровням сложности без запуска сайта.


### `scripts/run_site.py`

Назначение:

- запуск отдельного локального сайта генерации ученических листов.


### `scripts/kb_server.mjs`

Назначение:

- локальный launcher базы знаний (TriliumNext Trilium) без docker;
- находит собранный checkout, создаёт каталог данных с loopback config.ini,
  инициализирует свежую БД; слушает `127.0.0.1:8481`.


### `scripts/kb.mjs`

Назначение:

- CLI агентов к базе знаний через ETAPI (без зависимостей);
- команды `info/ensure/put/get/append/tree/search` и `sync-out`/`sync-in`
  (markdown-зеркало `knowledge/` для git);
- контракт — `Docs/KNOWLEDGE_BASE.md`.


## Папка `knowledge/`

Назначение:

- отслеживаемое git-зеркало дерева заметок базы знаний (истина для синхронизации
  между разработчиками; у каждого свой локальный Trilium);
- ветка дерева → каталог + `_note.md`, лист → `<название>.md`.


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


### `outputs/generated/worksheet_5_math_problems_example.json`

Назначение:

- готовый пример данных для листа `worksheet_5_tasks.json`;
- содержит дату, пути к логотипу и QR-коду и 5 арифметических задач;
- совместим с `scripts/render_worksheet.py`.


### `outputs/generated/all_tasks_tree_view.html`

Назначение:

- локальная HTML-страница с интерактивным деревом корпуса задач;
- позволяет раскрывать темы, выбирать ветки сложности и читать содержимое выбранного узла;
- построена как обзорный артефакт поверх `data/source_index/all_tasks_tree_by_theme_and_difficulty.md`.


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


### `tests/fixtures/problems_bundle.json`

Назначение:

- фикстура формата `{header, problems}` из 5 задач для теста загрузчика задач-бандла.


### `tests/fixtures/problems_plain_list.json`

Назначение:

- фикстура формата plain-массива из 12 задач с полем `condition` для теста загрузчика простого списка.


### `tests/test_story_worlds.py`

Назначение:

- проверяет корректность общего слоя сюжетных миров.


### `tests/test_olympiad_logic.py`

Назначение:

- проверяет генерацию олимпиадных шаблонов и `story metadata`.


### `tests/test_worksheet_renderer.py`

Назначение:

- проверяет загрузку JSON-шаблона листа;
- проверяет чтение задач из двух форматов JSON;
- проверяет понятные ошибки при несовпадении числа задач и переполнении слота.


### `tests/test_worksheet_service.py`

Назначение:

- проверяет валидацию списка сложностей 1–10;
- проверяет перевод числовой сложности в рабочие уровни генератора.


### `tests/test_template_generator.py`

Назначение:

- проверяет каталог шаблонов, безопасность `evaluate_formula` и целочисленность ответов;
- проверяет, что каждая `number_strategy` из JSON зарегистрирована и отношение не вырождается.


### `tests/__init__.py`

Назначение:

- делает `tests` пакетом, чтобы работала команда `python -m unittest tests.<модуль>`.


### `Docs/WORKSHEET_TEMPLATES.md`

Назначение:

- документация по JSON-шаблонам листов;
- описание формата, сценария подключения и команды запуска.


### `Docs/WEB_GENERATION.md`

Назначение:

- актуальный контракт локального сайта: быстрый вариант, ручной выбор,
  разделение проверяемого и архивного каталогов, печать и API `/generate`.


### `Docs/PROBLEM_TEMPLATES.md`

Назначение:

- документация по статичным математическим JSON-шаблонам;
- описание плейсхолдеров, ограничений, формул и добавления новых сюжетов.


### `data/templates/problem_templates.json`

Назначение:

- единственный каталог неизменяемых текстов математических задач;
- хранит классификацию, плейсхолдеры, числовые ограничения и формулы ответов;
- содержит стартовые и production-шаблоны, включая авторские записи групп A–K;
- используется каталогом, генератором задач и сайтом.


### `problemgen/catalog/problem_templates.py`

Назначение:

- загружает и валидирует JSON-каталог шаблонов;
- возвращает шаблоны и список тем для сайта;
- допускает текстовые плейсхолдеры, которые вычисляет `number_strategy` и которые не требуют числовых constraints.


### `problemgen/generation/template_generator.py`

Назначение:

- подбирает статичный шаблон и значения переменных;
- безопасно вычисляет формулу ответа;
- рендерит только плейсхолдеры, не меняя `template_text`;
- хранит реестр `number_strategy` для подбора целочисленных параметров под разные математические семьи;
- содержит стратегии и обратные проверки authoring-групп A–K, включая гарантированное деление A02.


### `scripts/generate_problem_from_template.py` и `scripts/generate_problem_set.py`

Назначение:

- CLI-запуск одной задачи и набора из пяти задач из JSON-шаблонов.


### `scripts/expand_problem_templates_from_tree.py`

Назначение:

- массово расширяет `data/templates/problem_templates.json` bridge-шаблонами;
- читает 100 leaf-ID из `data/source_index/math_problem_tree_template_ready.md`;
- создает по 9 записей на leaf в namespace `tree_*`;
- повторный запуск обновляет bridge-записи без добавления дубликатов.

### `scripts/build_all_tasks_corpus.py`

Назначение:

- ручной запуск полного pipeline для `Docs/all_tasks_all_files.md`;
- создает `All_tasks_structure_tree.json`, `All_tasks_templates.json`,
  `All_tasks_rejected_problems.json` и отчеты покрытия.


### `scripts/validate_all_tasks_corpus.py`

Назначение:

- проверяет уже созданные `All_tasks_*` файлы;
- валидирует покрытие задач шаблонами, дубликаты, плейсхолдеры и реконструкцию.


### `scripts/cleanup_all_tasks_templates.py`

Назначение:

- очищает `data/templates/All_tasks_templates.json`;
- пересобирает шаблоны из `source_text` так, чтобы переменными оставались только
  числовые `{number_N}`;
- пишет `data/templates/all_tasks_templates.json`,
  `data/templates/all_tasks_templates_rejected.json` и cleanup report.


### `scripts/validate_clean_all_tasks_templates.py`

Назначение:

- проверяет cleaned number-only каталог;
- валидирует формат placeholders, metadata, control chars и реконструкцию.


### `problemgen/source_index/all_tasks_pipeline.py`

Назначение:

- детерминированно извлекает задачи из read-only корпуса;
- чистит очевидные OCR-артефакты;
- классифицирует каждую задачу в один primary module;
- создает один шаблон на каждую валидную задачу;
- пишет дерево, rejected-файл, шаблоны и отчеты.


### `problemgen/source_index/answer_definition_cleanup.py`

Назначение:

- валидирует `answer_type` и безопасные `answer_formula` для очищенного архива;
- содержит белый список helper-функций, которыми recovery-слой пользуется для
  календарных и других нетривиальных вычислений;
- вычисляет контрольный ответ на `original_values`.

Ключевые сущности:

- `SAFE_HELPERS`;
- `calendar_condition_target_day(...)`;
- `birthday_same_weekday_gap(...)`;
- `may_sunday_noon_day_after_hours(...)`;
- `evaluate_formula(...)`;
- `validate_answer_definition(...)`.


### `data/source_index/All_tasks_structure_tree.json`

Назначение:

- полное дерево модулей по `Docs/all_tasks_all_files.md`;
- каждая валидная задача находится ровно в одном модуле.


### `data/templates/All_tasks_templates.json`

Назначение:

- one-to-one каталог шаблонов по полному корпусу;
- каждый шаблон содержит видимый номер, source problem ID, исходный текст,
  `template_text`, плейсхолдеры и `original_values`.


### `data/templates/all_tasks_templates.json`

Назначение:

- очищенный number-only каталог шаблонов;
- в `template_text` разрешены только placeholders вида `{number_N}`;
- имена, локации, предметы, единицы и обычные слова остаются literal text.


### `data/templates/all_tasks_answer_recovery.json`

Назначение:

- накладной каталог вручную проверенных `answer_type` и `answer_formula` для
  отдельных записей очищенного архива;
- хранит ожидаемый ответ на исходных числах, способ проверки и, если нужны
  связанные значения, `generation_strategy` для корректного нового варианта;
- сейчас покрывает арифметические цепочки, интервалы делимости, системы,
  турниры на выбывание, включение-исключение, строгие интервалы нечётных
  чисел, трёхзначные интервальные модели, базовые комбинаторные подсчёты
  слов/перестановок, движение, календарные инварианты, целочисленные
  сюжеты про время, разрезанные/окрашенные кубы и сеточные перегородки с
  внутренними дырками;
- используется `problemgen/worksheet/all_tasks_site.py` для отдельного
  ручного модуля с вычисляемыми ответами;
- не изменяет `all_tasks_templates.json` и read-only корпус.


### `tests/test_worksheet_site.py`

Назначение:

- проверяет архивный overlay с формулами ответов для `all_tasks_templates.json`;
- сверяет `source_answer`, счётчики восстановления и генерацию связанных
  геометрических, временных и кинематических параметров через
  `generation_strategy`;
- использует `problemgen/worksheet/all_tasks_site.py` и
  `problemgen/web/worksheet_site.py`.


### `data/templates/all_tasks_templates_rejected.json`

Назначение:

- rejected-записи после очистки number-only каталога;
- сохраняет исходный `template_number`, `template_id`, source mapping и причину.


### `data/templates/all_tasks_templates_cleanup_report.md`

Назначение:

- отчет очистки шаблонов: counts, repairs, rejected, manual review, validation commands.


### `data/templates/all_tasks_answer_definition_cleanup_report.md`

Назначение:

- отчет фильтрации `all_tasks_templates.json` по обязательным полям
  `answer_type` и `answer_formula`;
- содержит supported answer type allowlist, removed templates, rejected reasons
  и команды проверки.


### `data/source_index/All_tasks_rejected_problems.json`

Назначение:

- список записей, которые нельзя безопасно восстановить как математические задачи.


### `data/source_index/All_tasks_modules_summary.md`

Назначение:

- обзор модулей, количества задач, диапазонов сложности и примеров.


### `data/templates/All_tasks_template_coverage_report.md`

Назначение:

- отчет покрытия: сколько задач извлечено, сколько шаблонов создано, сколько
  реконструкций прошло, есть ли пропуски или дубликаты.


### `scripts/replace_bridge_leaf.py`

Назначение:

- атомарно заменяет bridge-шаблоны одного листа на переданные авторские записи;
- удаляет только записи целевого `source_tree_leaf` и одновременно отмечает его строки в ворклисте как `done`;
- используется авторами тематических веток при по-листовой миграции каталога.


### `scripts/replace_group_k_templates.py`

Назначение:

- воспроизводимый аудитный скрипт авторского батча K01–K08;
- заменяет записи группы K в каталоге и синхронно отмечает связанные строки ворклиста;
- используется только при повторной проверке или пересборке этого батча.


### `tests/test_h_grid_solid_templates.py`

Назначение:

- независимо перебирает перегородки сетки и сверяет ответы шаблонов H01–H09;
- использует `problemgen/generation/template_generator.py` и runtime-каталог шаблонов.


### `tests/test_template_generator.py`

Назначение:

- проверяет уникальность и валидность каталога;
- проверяет целочисленные ответы и валидацию пяти элементов листа;
- содержит независимые проверки формул и генераций для групп C, F, G, I и K.


### `data/templates/problem_sets/`

Назначение:

- верхний каталог тематических наборов шаблонов задач;
- каждый набор хранится в отдельной папке с собственным `templates.json` и `README.md`;
- общий список наборов лежит в `data/templates/problem_sets/catalog.json`.


### `data/templates/problem_sets/arithmetic/templates.json`

Назначение:

- новый каталог параметрических шаблонов по `docs/01_arifmeticheskie_vychisleniya_updated.md`;
- покрывает все 75 исходных номеров ровно один раз через `source_problem_numbers`;
- хранит независимые параметры, derived-поля, constraints, strategy names и metadata.


### `problemgen/generation/arithmetic_templates.py`

Назначение:

- загружает и валидирует `data/templates/problem_sets/arithmetic/templates.json`;
- генерирует новые арифметические задачи по выбранному `template_id`;
- считает ответы, проверяет целочисленность, последовательности и общий множитель;
- собирает JSON-структуру листа из ровно пяти выбранных модулей для сайта;
- при выборе модуля `arithmetic` случайно выбирает конкретный шаблон внутри него.


### `scripts/validate_arithmetic_templates.py`

Назначение:

- запускает deterministic validation нового арифметического каталога;
- проверяет каждый шаблон на 100 seeded-прогонах.


### `scripts/generate_arithmetic_worksheet.py`

Назначение:

- генерирует пример JSON-листа из пяти арифметических шаблонов;
- используется для ручной проверки fixed-seed генерации.


### `tests/test_arithmetic_templates.py`

Назначение:

- проверяет покрытие 75 source problem numbers;
- проверяет уникальность шаблонов, генерацию на 100 seed-значениях и правила листа из пяти задач.


### `docs/arithmetic_templates.md`

Назначение:

- объясняет JSON-схему арифметических шаблонов;
- показывает команды запуска генератора, сайта и тестов.


### `data/templates/problem_sets/equations/templates.json`

Назначение:

- хранит шаблоны уравнений и неравенств по отдельному исходному файлу;
- покрывает исходные номера через `source_problem_numbers`.


### `data/templates/problem_sets/systems_of_equations/templates.json`

Назначение:

- хранит шаблоны систем линейных уравнений;
- группирует дубликаты источника и сохраняет структуру коэффициентов.


### `data/templates/problem_sets/comparison_of_numbers_and_expressions/templates.json`

Назначение:

- хранит общий пул шаблонов сравнения чисел и выражений;
- объединяет задачи с персонажами и без персонажей в одном модуле.


### `Docs/OLYMPIAD_AUTHORING.md`

Назначение:

- описывает отдельный олимпиадный трек подготовки к ФМЛ 239;
- фиксирует правила изоляции каталога, стартовые шаблоны и дальнейшие треки авторинга;
- используется вместе с `data/templates/olympiad_templates.json` и `problemgen/generation/template_generator.py`.


### `data/templates/olympiad_templates.json`

Назначение:

- отдельный каталог олимпиадных шаблонов, не смешиваемый с `problem_templates.json`;
- содержит пометку `olympiad: true`, оригинальные названия тем и стартовые задачи по арифметике, системам, головоногам и чётности;
- загружается через параметр `catalog_path` генератора шаблонов.


### `data/templates/problem_sets/sequences_progressions_and_sums/templates.json`

Назначение:

- единый каталог из 9 уникальных структур последовательностей, прогрессий и сумм;
- учитывает 23 номера двух исходных файлов ровно по одному разу, объединяя повторы;
- хранит метки для задач с одним персонажем и без персонажей.

Связи:

- загружается и проверяется `problemgen/generation/sequence_templates.py`;
- выдаётся на сайт через `problemgen/web/worksheet_site.py`.


### `problemgen/generation/sequence_templates.py`

Назначение:

- безопасно генерирует последовательности и точные целочисленные ответы;
- проверяет арифметические прогрессии, чередующиеся шаги и знаки, циклические сдвиги и рекурсии modulo 10;
- для задач о цифрах строит интервал обратно и независимо проверяет единственность ответа;
- выбирает одного утверждённого персонажа из одной вселенной и согласует форму «заметил/заметила».


### `tests/test_sequence_templates.py`

Назначение:

- проверяет учёт исходных номеров, 200 seeded-прогонов каждого шаблона, циклы рекурсий, персонажей и смешанный лист.


### `scripts/validate_sequence_templates.py`

Назначение:

- ручная deterministic-проверка 200 экземпляров каждого шаблона последовательностей.


### `docs/sequence_templates.md`

Назначение:

- краткая русская инструкция к каталогу, генератору, правилам персонажей и командам проверки.


### `data/templates/problem_sets/integer_interval_counting/templates.json`

Назначение:

- хранит 5 уникальных шаблонов подсчёта чётных, нечётных и натуральных чисел в промежутках;
- объединяет повторы 14 исходных номеров без влияния на выбор шаблона.

Связи:

- используется `problemgen/generation/integer_interval_templates.py` и сайтом листов.


### `data/templates/problem_sets/integer_interval_counting/README.md`

Назначение:

- описывает источник, состав набора и команды проверки модуля промежутков.


### `problemgen/generation/integer_interval_templates.py`

Назначение:

- считает включённые промежутки постоянной формулой и проверяет её перебором;
- явно различает включённые и исключающие границы;
- точно считает числа с заданной цифрой.


### `tests/test_integer_interval_templates.py`

Назначение:

- проверяет учёт источника, четыре сочетания чётности границ, цифры и 500 генераций каждого шаблона.


### `docs/integer_interval_templates.md`

Назначение:

- русская инструкция к каталогу, формулам и запуску проверок.


### `scripts/validate_integer_interval_templates.py`

Назначение:

- вручную запускает 500 deterministic-проверок для каждого шаблона модуля промежутков.


### `data/templates/problem_sets/divisibility_multiples_remainders_primes/templates.json`

Назначение:

- хранит единый каталог задач делимости из двух источников, включая неактивную неоднозначную запись №638.

Связи:

- загружается `problemgen/generation/divisibility_templates.py` и подключается к сайту листов.


### `problemgen/generation/divisibility_templates.py`

Назначение:

- генерирует точные задачи о кратных, делимости, цифрах, мёде и конфетах;
- не выбирает неактивные записи и использует НОК для составной проверки делимости.


### `data/templates/problem_sets/digits_number_notation_and_cryptarithms/templates.json`

Назначение:

- единый каталог 45 структур по двум read-only digits-источникам;
- учитывает 129 исходных номеров ровно по одному разу;
- отделяет 26 активных проверяемых шаблонов от 19 неподдерживаемых форматов.

Связи:

- загружается `problemgen/generation/digits_templates.py`;
- активные записи доступны через `problemgen/web/worksheet_site.py`.


### `problemgen/generation/digits_templates.py`

Назначение:

- реализует точные счётчики цифр, digit-sum DP, перестановки, подпоследовательности, конечный поиск и именованные стратегии;
- гарантирует bounded generation, fixed seed и выбор персонажей одной вселенной.


### `tests/test_digits_templates.py`

Назначение:

- проверяет source accounting, независимые малые переборы, детерминизм, персонажей и интеграцию сайта.


### `scripts/validate_digits_templates.py`

Назначение:

- выполняет 300 deterministic-прогонов каждого из 26 активных шаблонов.


### `docs/digits_and_cryptarithms_templates.md`

Назначение:

- русская инструкция по каталогу, стратегиям, персонажам и проверкам digits-модуля.


### `docs/digits_grammar_audit.md`

Назначение:

- фиксирует объём и результат кросс-модульной проверки именованных шаблонов.
