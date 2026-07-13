# Problem Templates

## Зачем нужны шаблоны

Шаблон задачи отличается от готовой задачи. В шаблоне хранится неизменяемый `template_text` с плейсхолдерами, математическая формула и ограничения на переменные. Готовая задача появляется только после того, как генератор выбрал шаблон и подставил числа и персонажей.

Источник шаблонов: `data/templates/problem_templates.json`.

Генератор не перефразирует исходные задачи и не меняет `template_text` во время работы. Его путь строго такой:

```text
module + difficulty -> JSON template -> variables -> answer_formula -> rendered problem_text
```

## Структура записи

Каждая запись содержит:

- `template_id` — уникальный идентификатор;
- `domain`, `module`, `topic`, `problem_type` — место в дереве задач;
- `difficulty` и `supported_difficulties` — номинальная сложность и допустимые уровни 1–10;
- `template_text` — условие с плейсхолдерами;
- `placeholders` и `constraints` — роли, числа и границы чисел;
- `number_strategy` — имя общего алгоритма подбора чисел;
- `answer_formula` — арифметическая формула ответа;
- `derived_words` — правила выбора русской формы слова.

Пример:

```json
{
  "template_id": "movement_together_001",
  "module": "movement",
  "template_text": "{character_1} и {character_2} идут по одной дороге...",
  "answer_formula": "duration * (speed_1 + speed_2)",
  "integer_answer_required": true
}
```

## Как добавить шаблон

1. Добавить новую запись в массив `templates` файла `data/templates/problem_templates.json`.
2. Указать все обязательные классификаторы и уникальный `template_id`.
3. Описать каждый плейсхолдер и ограничения для всех чисел.
4. Использовать существующую `number_strategy` либо добавить новую функцию с декоратором `@_number_strategy("имя")` в `problemgen/generation/template_generator.py`.
5. Запустить `python -m unittest tests.test_template_generator` (или весь набор через `python -m unittest discover -s tests`).

Новые сюжеты одного математического типа добавляются отдельными JSON-записями с той же математической стратегией, но другим `template_text`.

## Связь с production-деревом

Файл `data/source_index/math_problem_tree_template_ready.md` задает, какие темы
нужно переводить в рабочие JSON-шаблоны. После его добавления каталог
`data/templates/problem_templates.json` расширен с 9 до 59 шаблонов.

Новые production-шаблоны сделаны сложнее стартовых: в них есть задержки,
переносы, удаление части объектов, несколько платежей, две покупки или
дополнительные ограничения. Такие задачи обычно требуют 3-5 действий решения.

Добавленные модули и семейства:

- `ages` -> `ages_joining_group_001`
- `ratios` -> `ratio_transfer_001`
- `heads_and_legs` -> `heads_and_legs_removed_001`
- `joint_work` -> `joint_work_delay_001`
- `round_robin` -> `round_robin_missing_001`
- `paint_cube` -> `paint_cube_unpainted_001`
- `movement` -> `movement_two_stage_001`
- `opposite_motion` -> `opposite_motion_delay_001`
- `factor_shortcut` -> `factor_shortcut_compare_001`
- `price_system` -> `price_system_two_receipts_001`

Дополнительная партия из 40 шаблонов добавлена как варианты этих же production-семейств:
`ages_joining_group_002`-`005`, `ratio_transfer_002`-`005`,
`heads_and_legs_removed_002`-`005`, `joint_work_delay_002`-`005`,
`round_robin_missing_002`-`005`, `paint_cube_unpainted_002`-`005`,
`movement_two_stage_002`-`005`, `opposite_motion_delay_002`-`005`,
`factor_shortcut_compare_002`-`005`, `price_system_two_receipts_002`-`005`.

## Массовое покрытие дерева

Для быстрого покрытия всех 100 листьев дерева добавлен скрипт
`scripts/expand_problem_templates_from_tree.py`.

Что он делает:

- читает `data/source_index/math_problem_tree_template_ready.md`;
- создает по 9 bridge-шаблонов на каждый leaf-ID;
- добавляет записи с `template_id` вида `tree_a01_ratio_transfer_02`;
- кладет их в отдельные модули `tree_*`, чтобы не смешивать scaffold-покрытие
  со старыми ручными модулями `ratios`, `ages`, `movement` и т. д.;
- сохраняет исходную связь через поля `source_tree_leaf` и `source_tree_module`;
- повторный запуск обновляет уже созданные `tree_*` записи, но не добавляет
  дубликаты.

Важно: эти 900 записей — bridge-coverage слой. Они дают каждому пункту дерева
рабочее место в JSON-каталоге и проверяемую генерацию с целыми ответами, но не
заменяют будущие точные, вручную написанные шаблоны для каждого математического
типа. Когда leaf становится приоритетным, его bridge-шаблон нужно заменить или
дополнить более специальной `number_strategy`.

Если следующий шаблон берется из `math_problem_tree_template_ready.md`, сначала
проверь поле `Production template family`, затем добавь JSON-запись и только при
необходимости новую `number_strategy`.

## Масштабирование: почему архитектура не расползается

При росте каталога важно различать две оси роста и держать их раздельно.

- **Новый сюжет того же типа математики** — это только JSON. Добавляется запись в
  `problem_templates.json` с существующей `number_strategy` и `answer_formula`.
  Python не трогается. Так растёт большая часть каталога.
- **Новый тип математики** — это одна маленькая функция в
  `problemgen/generation/template_generator.py`, помеченная декоратором
  `@_number_strategy("имя")`, плюс JSON-запись, которая на неё ссылается.

Стратегии подбора чисел хранятся в **реестре** `_NUMBER_STRATEGIES` (dict имя → функция),
а не в разрастающейся цепочке `if/elif`. Это даёт три гарантии при росте:

1. диспетчеризация по имени стратегии — O(1), список всех стратегий виден в одном месте;
2. `registered_strategies()` отдаёт множество доступных имён;
3. тест `test_every_template_strategy_is_registered` падает, если в JSON появилась
   запись со стратегией, для которой нет функции. Рассинхрон JSON и Python ловится
   на тестах, а не в проде.

Каталог читается и валидируется **один раз** и кэшируется (`_read_and_validate`,
`functools.lru_cache`). Ключ кэша — путь файла и его время изменения (`st_mtime_ns`),
поэтому после правки `problem_templates.json` запись перечитывается автоматически, без
перезапуска процесса. `load_template_catalog` возвращает свежую копию списка, так что
вызывающий код не может испортить кэш.

Правило на будущее: если для новой темы хочется просто «слегка другую» математику —
сначала проверь, нельзя ли выразить её существующей стратегией и другой
`answer_formula`. Новую стратегию заводи, только когда меняется сам алгоритм подбора
чисел, а не формула ответа.

## Запуск одной задачи

```bash
python scripts/generate_problem_from_template.py --module joint_work --difficulty 4
```

Команда печатает JSON с `problem_text`, отдельным `answer` и фактическими `variables`.
