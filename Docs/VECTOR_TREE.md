# Vector Tree

Это короткая смысловая навигация по проекту после перехода на модульную архитектуру.


## Если нужен верхний запуск проекта

Смотреть:

- `02.py`
- `problemgen/cli.py`

Что искать:

- `main()`
- `parse_args()`
- `run_cli(...)`


## Если нужен общий оркестратор генерации

Смотреть:

- `problemgen/app.py`

Что искать:

- `build_domain_catalog()`
- `get_domain(...)`
- `generate_problem_bundle(...)`


## Если нужно чинить русский язык сразу для всех новых задач

Смотреть:

- `problemgen/russian/agreement.py`
- `problemgen/russian/validator.py`
- `problemgen/russian/lexicon.py`

Что искать:

- `pluralize_ru(...)`
- `count_with_word_ru(...)`
- `attach_language_report(...)`
- `NounForms`


## Если нужно добавить новый математический блок

Смотреть:

- `problemgen/domains/base.py`
- `problemgen/domains/`
- `problemgen/app.py`

Что делать:

1. создать новую папку домена;
2. добавить `domain.py`;
3. добавить `templates.py`;
4. зарегистрировать домен в `build_domain_catalog()`.


## Если нужны задачи на счет

Смотреть:

- `problemgen/domains/counting/domain.py`
- `problemgen/domains/counting/templates.py`

Что искать:

- `CountingDomain`
- `COUNTING_RANGES`
- `generate_total_groups(...)`
- `generate_missing_group(...)`


## Если нужна комбинаторика

Смотреть:

- `problemgen/domains/combinatorics/domain.py`
- `problemgen/domains/combinatorics/templates.py`

Что искать:

- `CombinatoricsDomain`
- `COMBINATORICS_RANGES`
- `generate_outfit_pairs(...)`
- `generate_route_pairs(...)`


## Если нужны задачи на отрезки

Смотреть:

- `problemgen/domains/segments/domain.py`
- `problemgen/domains/segments/legacy_engine.py`

Что искать:

- `SegmentsDomain`
- `SEGMENT_TEMPLATE_LABELS`
- `generate_problem_set(...)`
- `TemplateRegistry`
- шаблоны `Line*` и `Plane*`


## Если нужно менять уровни сложности

Смотреть:

- `problemgen/core/difficulty.py`
- для доменных диапазонов: `templates.py` нужного домена
- для legacy-отрезков: `problemgen/domains/segments/legacy_engine.py`

Что искать:

- `DIFFICULTY_LEVELS`
- `COUNTING_RANGES`
- `COMBINATORICS_RANGES`
- `DIFFICULTY_PROFILES`


## Если нужны темы, персонажи и локации

Смотреть:

- `problemgen/core/themes.py`
- для legacy-отрезков: `problemgen/domains/segments/legacy_engine.py`

Что искать:

- `THEMES`
- `ThemeConfig`
- `sample_theme(...)`
- `STORY_THEME_LABELS`
- `THREE_OBJECT_STORY_SCENES`
- `FOUR_OBJECT_STORY_SCENES`


## Если нужно проверить размерности `см / м / км`

Смотреть:

- `problemgen/core/themes.py`
- `problemgen/russian/validator.py`
- `problemgen/domains/segments/legacy_engine.py`

Что искать:

- поле `unit_short`
- `format_distance(...)`
- `validate_problem_record(...)`


## Если нужен веб-интерфейс

Смотреть:

- `problemgen/web/server.py`
- `frontend/styles.css`
- `frontend/app.js`

Что искать:

- `render_page(...)`
- `render_problem_cards(...)`
- `ProblemWebHandler`
- `create_http_server(...)`
- `syncDomainOptions()`


## Если нужно понять, где лежат итоговые JSON

Смотреть:

- `output/`
- `.gitignore`

Важно:

- итоговый файл переписывается финальной версией после общей языковой проверки в `problemgen/app.py`.
- папка `output/` не должна попадать в git по умолчанию.


## Если нужно понять, что менялось недавно

Смотреть:

- `Docs/WORK_LOG.md`
