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
