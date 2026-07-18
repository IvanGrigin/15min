# Vector Tree

- Если нужен модуль «Отношения, доли, пропорции и проценты» → `Docs/ratio_templates.md` → `data/templates/problem_sets/ratios_fractions_proportions_and_percentages/` → `problemgen/generation/ratio_templates.py` → `problemgen/web/worksheet_site.py`.

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
- `problemgen/source_index/`
- `problemgen/generation/`
- `problemgen/language/`

Что искать:

- `All_tasks_structure_tree.json`
- `All_tasks_templates.json`
- `All_tasks_template_coverage_report.md`
- `all_tasks_templates.json`
- `all_tasks_templates_cleanup_report.md`
- `scripts/build_all_tasks_corpus.py`
- `scripts/validate_all_tasks_corpus.py`
- `scripts/cleanup_all_tasks_templates.py`
- `scripts/validate_clean_all_tasks_templates.py`


## Если нужно пересобрать полный корпус `all_tasks_all_files`

Смотреть:

- `Docs/all_tasks_all_files.md`
- `problemgen/source_index/all_tasks_pipeline.py`
- `scripts/build_all_tasks_corpus.py`
- `scripts/validate_all_tasks_corpus.py`

Что искать:

- `extract_records(...)`
- `classify_problem(...)`
- `build_tree(...)`
- `build_templates(...)`
- `validate_outputs(...)`


## Если нужно очистить шаблоны до number-only формата

Смотреть:

- `data/templates/All_tasks_templates.json`
- `data/templates/all_tasks_templates.json`
- `problemgen/source_index/template_cleanup.py`
- `scripts/cleanup_all_tasks_templates.py`
- `scripts/validate_clean_all_tasks_templates.py`

Что искать:

- `clean_template_record(...)`
- `parameterize_numbers_only(...)`
- `validate_clean_catalog(...)`
- `{number_N}`


## Если нужно понять старое bridge-покрытие дерева

Смотреть:

- `data/source_index/math_problem_tree_template_ready.md`
- `data/templates/problem_templates.json`
- `scripts/expand_problem_templates_from_tree.py`
- `Docs/PROBLEM_TEMPLATES.md`

Что искать:

- `source_tree_leaf`
- `source_tree_module`
- `tree_*`
- `bridge template`

Важно:

- это scaffold-слой, а не новый one-to-one каталог для корпуса;
- для полного корпуса использовать `All_tasks_templates.json`.


## Если нужно собрать лист с задачами в PDF или PNG

Смотреть:

- `Docs/WORKSHEET_TEMPLATES.md`
- `data/templates/worksheets/`
- `problemgen/io/worksheet_renderer.py`
- `scripts/render_worksheet.py`
- `assets/`

Что искать:

- `worksheet_5_tasks.json`
- `load_worksheet_template(...)`
- `load_problem_texts(...)`
- `render_worksheet(...)`


## Если нужен сайт с быстрым вариантом и печатью

Смотреть:

- `Docs/WEB_GENERATION.md`
- `problemgen/web/worksheet_site.py`
- `frontend/worksheet_site.css`
- `frontend/worksheet_site.js`
- `scripts/run_site.py`

Что искать:

- `generate_random_worksheet(...)` — вариант в одну кнопку из модулей с
  проверяемыми ответами;
- `generate_combined_worksheet_by_modules(...)` — ручная сборка и архивный
  модуль;
- `task-count` — управление числом задач от 1 до 20;
- `print-with-answers` — CSS-режим A4 landscape с отрезаемой колонкой и
  фирменным знаком/QR справа;
- `POST /generate`

Если нужны все подготовленные тексты корпуса, а не только проверяемые ответы:

- `data/templates/all_tasks_templates.json` — 1088 очищенных активных
  шаблонов;
- `data/templates/all_tasks_templates_rejected.json` — исключённые фрагменты;
- `data/templates/all_tasks_answer_recovery.json` — отдельный проверяемый
  overlay для уже разобранных формул, не меняющий архив;
- `problemgen/worksheet/all_tasks_site.py` — загрузка overlay, проверка
  исходного ответа, стратегии связанных параметров для кубов, сеточных дырок,
  временных сюжетов и движения и безопасный fallback без выдумывания ответов.

Если нужно добавить корректный шаблон или восстановить ответ:

- сначала открыть `Docs/TEMPLATE_AUTHORING_GUIDE.md` и выбрать ровно один путь:
  production, archive recovery или олимпиадный каталог;
- для production смотреть `Docs/PROBLEM_TEMPLATES.md` и
  `problemgen/generation/template_generator.py`;
- для archive recovery смотреть `data/templates/README.md`,
  `problemgen/worksheet/all_tasks_site.py` и `tests/test_worksheet_site.py`.


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
- `Docs/source_documents/README.md` — импортированные источники, ещё не включённые в индекс
- `data/source_index/README.md`
- `data/source_index/task_tree/README.md`
- `data/source_index/task_tree/manifest.json`
- `data/source_index/tasks_index.example.json`
- `data/source_index/source_groups.example.json`

Важно:

- исходный файл не менять;
- разметку вести отдельно.

Если нужно работать с новым импортированным сборником, сначала открыть его в
`Docs/source_documents/`, затем создать отдельную производную разметку в
`data/source_index/`; не дописывать его задачи в `all_tasks_all_files.md`.

Если нужна именно быстрая тематическая навигация по корпусу:

- смотреть `data/source_index/task_tree/README.md`
- выбрать раздел, затем один тематический лист; листы не превышают 160 строк

Если нужно понять, какие темы переводить в production JSON-шаблоны:

- открыть нужный лист в `data/source_index/task_tree/`
- раздел `Production planning` связывает тему с будущим `module`, семейством шаблона, переменными, валидатором и минимумом действий
- дерево — это планирование и индекс, а не подтверждение реализации шаблона в runtime

Если нужен удобный визуальный просмотр в браузере:

- смотреть `outputs/generated/all_tasks_tree_view.html`
- там реализовано интерактивное дерево с раскрывающимися ветками и правой панелью выбранного узла


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

Если нужен отдельный трек подготовки к ФМЛ 239:

- смотреть `Docs/OLYMPIAD_AUTHORING.md`;
- использовать только `data/templates/olympiad_templates.json` и модули `olymp_*`;
- вызывать `generate_problem_from_template(..., catalog_path="data/templates/olympiad_templates.json")`, не смешивая его с каталогом 15-минуток.


## Если нужны задачи на отрезки

Смотреть:

- `problemgen/domains/segments/domain.py`
- `problemgen/domains/segments/legacy_engine.py`


## Если нужно менять уровни сложности

Смотреть:

- `problemgen/core/difficulty.py`
- для доменных диапазонов: `templates.py` нужного домена
- для legacy-отрезков: `problemgen/domains/segments/legacy_engine.py`

Для листов с 5 задачами:

- `problemgen/worksheet/service.py`


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

Если нужен готовый пример данных для листа на 5 задач:

- `outputs/generated/worksheet_5_math_problems_example.json`


## Если нужно понять, что менялось недавно

Смотреть:

- `Docs/WORK_LOG.md`


## Если нужно понять, какая тематическая группа сейчас занята

Смотреть:

- `Docs/AGENT_STATUS.md`

Это единственный источник правды: там указаны владелец, ветка, статус и
прогресс. Статус «готово (только перепроверка)» означает, что авторинг завершён
и допустимы только ревью и исправления по его результатам.


## Если нужны статичные шаблоны задач

Смотреть:

- `Docs/PROBLEM_TEMPLATES.md`
- `data/source_index/math_problem_tree_template_ready.md`
- `data/templates/problem_templates.json`
- `problemgen/catalog/problem_templates.py`
- `problemgen/generation/template_generator.py`

Что искать:

- production-листья `P1`/`P2` в `math_problem_tree_template_ready.md`
- JSON-записи с `template_text`, `constraints`, `number_strategy`, `answer_formula`
- зарегистрированные функции `@_number_strategy(...)`

После интеграции authoring-групп A–K:

- для гарантированного целого деления и обратной проверки смотреть `arithmetic_a02_nested_expression` в `problemgen/generation/template_generator.py`;
- для авторских календарных и часовых шаблонов использовать I01–I08 из каталога и независимые тесты в `tests/test_template_generator.py`;
- для сеток и объёмной геометрии смотреть `tests/test_h_grid_solid_templates.py`;
- прогресс one-to-one ворклиста фиксируется в `data/source_index/per_task_template_worklist.json` и `Docs/AGENT_STATUS.md`.

Если нужен лист из пяти выбранных тем:

- `problemgen/worksheet/service.py`
- `problemgen/web/worksheet_site.py`
- `Docs/WEB_GENERATION.md`


## Если нужно добавить новый тематический набор шаблонов

Смотреть:

- `data/templates/problem_sets/`
- `data/templates/problem_sets/catalog.json`

Что делать:

- создать папку `data/templates/problem_sets/<id>/`
- положить туда `templates.json` и `README.md`
- добавить запись в `data/templates/problem_sets/catalog.json`


## Если нужны арифметические шаблоны из `01_arifmeticheskie_vychisleniya_updated.md`

Смотреть:

- `data/templates/problem_sets/arithmetic/templates.json`
- `problemgen/generation/arithmetic_templates.py`
- `docs/arithmetic_templates.md`
- `tests/test_arithmetic_templates.py`
- `scripts/validate_arithmetic_templates.py`
- `scripts/generate_arithmetic_worksheet.py`

Что искать:

- `source_problem_numbers` для покрытия всех 75 исходных номеров
- `generation_strategy` для связи JSON с Python-логикой
- `generate_arithmetic_worksheet_by_modules(...)` для сайта с выбором ровно пяти модулей


## Если нужны последовательности, прогрессии и суммы

Смотреть:

- `data/templates/problem_sets/sequences_progressions_and_sums/templates.json`
- `problemgen/generation/sequence_templates.py`
- `tests/test_sequence_templates.py`
- `docs/sequence_templates.md`

Что искать:

- `recurrence_value(...)` для конечного обнаружения цикла modulo 10;
- `solve_digit_count_intervals(...)` для независимой проверки единственности;
- `generate_sequence_problem_from_module(...)` для выбора одного шаблона в общем пуле.


## Если нужен подсчёт целых чисел в промежутках

Смотреть:

- `data/templates/problem_sets/integer_interval_counting/templates.json`
- `problemgen/generation/integer_interval_templates.py`
- `tests/test_integer_interval_templates.py`
- `docs/integer_interval_templates.md`

Что искать:

- `count_parity_inclusive(...)` для включённых границ;
- `count_parity_with_digit(...)` для точного условия на цифру;
- `interval_type` для различения включённого и исключающего промежутка.


## Если нужны задачи о делимости

Смотреть:

- `data/templates/problem_sets/divisibility_multiples_remainders_primes/templates.json`
- `problemgen/generation/divisibility_templates.py`
- `tests/test_divisibility_templates.py`

Что искать:

- `_count(...)` для открытых и включённых промежутков;
- `math.lcm(...)` для составных признаков делимости;
- `active: false` для безопасного учёта неоднозначного №638.


## Если нужны цифры, запись чисел и криптарифмы

Смотреть:

- `data/templates/problem_sets/digits_number_notation_and_cryptarithms/templates.json`
- `problemgen/generation/digits_templates.py`
- `tests/test_digits_templates.py`
- `docs/digits_and_cryptarithms_templates.md`
- `docs/digits_grammar_audit.md`

Что искать:

- `source_digits_problem_numbers()` для полного учёта двух read-only источников;
- `count_n_digit_numbers_with_digit_sum(...)` для точного DP;
- `digit_occurrences_in_range(...)` для подсчёта всех вхождений;
- `active: false` для структур, которые ответный рендерер пока не поддерживает.


## Если нужны множители, произведения и факториалы

Смотреть:

- `data/templates/problem_sets/factors_products_and_factorials/templates.json`
- `data/templates/problem_sets/factors_products_and_factorials/source_accounting.json`
- `problemgen/generation/factor_product_templates.py`
- `tests/test_factor_product_templates.py`
- `Docs/factor_product_templates.md`

Что искать:

- `minimum_factor_sum(...)` для точной оптимизации по парам делителей;
- `trailing_zeros_of_product(...)` для показателей степеней 2 и 5;
- manifest для полного учёта 31 уникального источника.
