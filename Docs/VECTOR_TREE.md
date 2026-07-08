# Vector Tree

Это короткая смысловая навигация по проекту после выравнивания структуры папок.


## Если нужен верхний запуск новой архитектуры

Смотреть:

- `scripts/run_problemgen.py`
- `problemgen/cli.py`

Что искать:

- `main()`
- `parse_args()`
- `run_cli(...)`


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
4. зарегистрировать домен в `build_domain_catalog()`;
5. если нужен отдельный запуск, добавить смысловой скрипт в `scripts/`.


## Если нужны задачи на счет

Смотреть:

- `problemgen/domains/counting/domain.py`
- `problemgen/domains/counting/templates.py`


## Если нужна комбинаторика

Смотреть:

- `problemgen/domains/combinatorics/domain.py`
- `problemgen/domains/combinatorics/templates.py`


## Если нужны задачи на отрезки

Смотреть:

- `problemgen/domains/segments/domain.py`
- `problemgen/domains/segments/legacy_engine.py`


## Если нужно менять уровни сложности

Смотреть:

- `problemgen/core/difficulty.py`
- для доменных диапазонов: `templates.py` нужного домена
- для legacy-отрезков: `problemgen/domains/segments/legacy_engine.py`


## Если нужны темы, персонажи и локации

Смотреть:

- `problemgen/core/themes.py`
- для legacy-отрезков: `problemgen/domains/segments/legacy_engine.py`


## Если нужен веб-интерфейс

Смотреть:

- `problemgen/web/server.py`
- `frontend/styles.css`
- `frontend/app.js`


## Если нужно понять, где лежат результаты генерации

Смотреть:

- `outputs/`
- `outputs/README.md`
- `.gitignore`

Важно:

- исходный код не должен сохраняться в `outputs/`;
- большие массовые выгрузки лучше хранить в отдельной подпапке внутри `outputs/`.


## Если нужно понять, что менялось недавно

Смотреть:

- `docs/WORK_LOG.md`
