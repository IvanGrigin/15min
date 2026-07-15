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
