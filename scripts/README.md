# Скрипты запуска

В этой папке лежат только запускаемые вручную сценарии.

Правило:

- переиспользуемую логику хранить в `problemgen/`;
- в `scripts/` оставлять короткие entry point-файлы;
- не создавать здесь безымянные файлы вида `17.py`, `28.py`, `new.py`.

Текущие скрипты:

- `run_problemgen.py` — основной запуск модульного генератора;
- `legacy_simple_generator.py` — ранний автономный генератор;
- `generate_friendship_class.py` — генератор JSON-набора задач про класс, дружбу и парты.
- `render_worksheet.py` — рендер листа с задачами по JSON-шаблону в `PDF` или `PNG`.
- `generate_problem_from_template.py` — печатает одну задачу из статичного JSON-шаблона по теме и сложности.
- `generate_problem_set.py` — сохраняет пять задач по JSON-списку тем и сложностей.
- `generate_worksheet.py` — генерация ученического листа по 5 выбранным темам и сложностям; старый флаг `--difficulties` сохранён.
- `run_site.py` — локальный сайт для генерации ученических листов по 5 выбранным темам и сложностям.
- `expand_problem_templates_from_tree.py` — идемпотентно расширяет `data/templates/problem_templates.json` bridge-шаблонами из `data/source_index/math_problem_tree_template_ready.md`.
- `build_all_tasks_corpus.py` — строит полное дерево `All_tasks_structure_tree.json` и one-to-one шаблоны `All_tasks_templates.json` из read-only корпуса `Docs/all_tasks_all_files.md`.
- `validate_all_tasks_corpus.py` — проверяет уже созданные `All_tasks_*` файлы: покрытие, дубликаты, плейсхолдеры и реконструкцию исходных задач.
- `cleanup_all_tasks_templates.py` — очищает `All_tasks_templates.json` в number-only каталог `all_tasks_templates.json`.
- `validate_clean_all_tasks_templates.py` — проверяет cleaned каталог: только `{number_N}`, metadata, control chars и реконструкцию.
- `cleanup_answer_definitions.py` — удаляет из `all_tasks_templates.json` шаблоны без валидных `answer_type` и `answer_formula`.
- `validate_answer_definitions.py` — проверяет, что в retained catalog не осталось missing/unknown answer definitions, undefined variables и missing validators.
- `validate_worksheet_site_catalog.py` — проверяет, сколько шаблонов из `all_tasks_templates.json` сайт может безопасно показывать в селекторах.
- `cleanup_all_tasks_template_texts.py` — чистит тексты задач в `all_tasks_templates.json`, чинит high-confidence OCR/нумерацию и переносит unrecoverable фрагменты в rejected.
- `validate_all_tasks_template_texts.py` — проверяет, что в активном каталоге нет fatal text-lint issues и пересечений с rejected.
- `replace_bridge_leaf.py` — заменяет bridge-шаблоны одного leaf авторскими записями из JSON-payload и синхронно обновляет ворклист.
- `replace_group_k_templates.py` — воспроизводит авторский батч шаблонов K01–K08 и синхронизирует связанные строки ворклиста.
- `rebuild_problem_templates_from_cleaned.py` — полностью пересобирает `data/templates/problem_templates.json` из `docs/cleaned_math_problems.md`.
- `validate_cleaned_problem_templates.py` — проверяет rebuilt-каталог: количество, уникальные ID, русские модули и последовательные `{number_N}`.
- `validate_arithmetic_templates.py` — проверяет новый каталог `data/templates/problem_sets/arithmetic/templates.json` на покрытие 75 исходных задач и 100 seeded-прогонов каждого шаблона.
- `generate_arithmetic_worksheet.py` — сохраняет пример JSON-листа из ровно пяти выбранных арифметических шаблонов.
- `build_equation_templates_from_source.py` — собирает каталог `equations` из исходного файла уравнений.
- `validate_equation_templates.py` — проверяет генерацию шаблонов уравнений.
- `validate_system_equation_templates.py` — проверяет генерацию шаблонов систем уравнений.
- `validate_comparison_templates.py` — проверяет генерацию шаблонов сравнения чисел и выражений.
- `validate_sequence_templates.py` — выполняет 200 deterministic-прогонов каждого шаблона последовательностей, прогрессий и сумм.
- `validate_integer_interval_templates.py` — выполняет 500 deterministic-прогонов каждого шаблона подсчёта чисел в промежутках.
- `validate_divisibility_templates.py` — выполняет 300 прогонов активных шаблонов делимости.
- `validate_digits_templates.py` — выполняет 300 deterministic-прогонов каждого активного digits-шаблона.
- `validate_ratio_templates.py` — выполняет 200 deterministic-прогонов каждого шаблона отношений, долей и процентов.
- `validate_factor_product_templates.py` — выполняет 300 deterministic-прогонов каждого шаблона модуля 09.
- `validate_combinatorics_templates.py` — выполняет 300 deterministic-прогонов каждого шаблона модуля 11.
- `validate_pigeonhole_templates.py` — выполняет 300 deterministic-прогонов каждого шаблона модуля 12.
- `validate_parity_templates.py` — выполняет 500 deterministic-прогонов шаблона модуля 13.
- `validate_process_templates.py` — выполняет 300 deterministic-прогонов каждого шаблона модуля 14.
- `validate_calendar_templates.py` — выполняет 200 deterministic-прогонов каждого шаблона модуля 15.
- `validate_clock_templates.py` — выполняет 200 deterministic-прогонов каждого шаблона модуля 16.
- `validate_time_zone_templates.py` — выполняет 200 deterministic-прогонов каждого шаблона модуля 17.
- `validate_motion_templates.py` — выполняет 200 deterministic-прогонов каждого шаблона модуля 18.
