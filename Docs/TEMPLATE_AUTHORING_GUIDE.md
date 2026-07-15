# Руководство: как писать шаблоны задач

Это полный справочник для авторинга шаблонов, которыми заменяются 900 bridge-заглушек.
Цель — чтобы генератор давал задачи **того же типа и качества**, что оригиналы
15-минуток из корпуса `Docs/all_tasks_all_files.md`, но с новыми числами и героями.

Связанные документы: [PROBLEM_TEMPLATES.md](PROBLEM_TEMPLATES.md) (обзор системы),
[PER_TASK_TEMPLATE_PLAN.md](PER_TASK_TEMPLATE_PLAN.md) (ворклист),
[AGENT_TASKS.md](AGENT_TASKS.md) (распределение работы).

## Конвейер

```text
module + difficulty
  -> выбор JSON-шаблона (data/templates/problem_templates.json)
  -> number_strategy подбирает числа (problemgen/generation/template_generator.py)
  -> answer_formula считает ответ (безопасный вычислитель)
  -> template_text.format(...) рендерит условие с героями и словоформами
```

Шаблон неизменяем: генератор не переписывает `template_text`, только подставляет.

## Анатомия шаблона

Обязательные поля: `template_id`, `domain`, `module`, `topic`, `problem_type`,
`difficulty`, `template_text`. Плюс:

| Поле | Правило |
|---|---|
| `template_id` | уникальный; для авторских — осмысленный, напр. `compare_triple_products_a04_001` |
| `module` | группирует шаблоны одной темы; по нему их находит генератор и сайт |
| `supported_difficulties` | список уровней 1–10, на которых шаблон валиден |
| `title` | человекочитаемое имя (нужно для списка модулей) |
| `template_text` | условие с плейсхолдерами `{var}` |
| `placeholders` | `{characters, locations, numbers}` — какие слоты бывают |
| `constraints` | границы для **каждого** числового слота (`type/min/max`) |
| `number_strategy` | имя функции подбора чисел |
| `answer_formula` | выражение ответа |
| `answer_type` | `number` (по умолч.) / `multi` / `text` |
| `integer_answer_required` | для `number` — требовать целый ответ |
| `derived_words` | правила русской словоформы: `{"number": "<num>", "forms": [ед, дв, мн]}` |
| `source_tree_leaf` | id листа дерева, который закрывает шаблон (напр. `A04`) |

Валидатор каталога проверяет: все поля на месте, `template_id` уникален, каждый
плейсхолдер из текста объявлен (в characters/locations/numbers/derived_words),
у каждого числа есть constraints, у каждой словоформы ровно 3 формы.

## Возможности движка ответа

`answer_formula` — это безопасное выражение (никакого произвольного кода):

- операторы `+ - * / // % **` (степень: целый показатель 0..64), унарный `-`;
- переменные из числовой стратегии и строковые константы;
- функции из белого списка: `abs, min, max, gcd, lcm, isqrt, comb, perm,
  digit_sum, count_digit(d, lo, hi), count_multiples(k, lo, hi), num_divisors,
  weekday_after(start, days), bigger_label(x, y)`;
- списки `[...]` для составных ответов (`answer_type = "multi"`).

Нужна функция, которой нет? Добавь одну строку в `_FUNCTIONS`
(`problemgen/generation/template_generator.py`) — это штатная точка роста.

`answer_type`:

- `number` — одно число (int/float);
- `text` — строка (напр. день недели через `weekday_after`);
- `multi` — список из нескольких ответов (напр. `[bigger_label(...), abs(...)]`).

## Числовая стратегия — главное правило

Стратегия объявляется декоратором и **обязана возвращать значения внутри
`constraints` своих шаблонов**. Рассинхрон стратегии и границ — это баг, который
роняет генерацию (см. историю «205 хрупких» в [WORK_LOG.md](WORK_LOG.md)).

```python
@_number_strategy("compare_triple_products")
def _compare_triple_products(difficulty: int, rng: random.Random) -> dict[str, int]:
    mid = rng.randint(2, 9) * (10 ** (difficulty % 3 + 1)) + rng.randint(0, 9)
    n = rng.randint(1000, 1000 + difficulty * 900)
    m = rng.randint(1000, 1000 + difficulty * 900)
    delta = rng.randint(1, 3)
    return {"a": n, "mid": mid, "b": m, "c": n - delta, "d": m + delta}
```

Требования:

- ответ должен получаться нужного типа (для `number` с `integer_answer_required` — целым);
- масштабировать сложность через `difficulty` (диапазоны шире на высоких уровнях);
- избегать вырожденных случаев (деление на 0, отношение 1:1, отрицательные количества);
- переиспользовать стратегию для нескольких сюжетов одной математики.

## Как заменить bridge-заглушку (полный цикл)

На примере листа `A04` (сравнение близких произведений):

1. **Разобрать оригиналы темы.** Открыть лист `data/source_index/task_tree/<группа>/A04.md`
   и записи корпуса; понять математический тип (не копировать OCR-шум, а
   воспроизвести тип задачи чисто).
2. **Стратегия.** Добавить `@_number_strategy(...)` в
   `problemgen/generation/template_generator.py` (если нет подходящей).
3. **Шаблон.** Написать авторский шаблон и вставить в каталог, одновременно удалив
   заглушки листа (у них `source_tree_leaf == "A04"`). Правку каталога делать
   скриптом (файл большой и машинно-сгенерированный), например:

   ```python
   import json
   p = "data/templates/problem_templates.json"
   d = json.load(open(p, encoding="utf-8"))
   d["templates"] = [t for t in d["templates"] if t.get("source_tree_leaf") != "A04"]
   d["templates"].append(NEW_TEMPLATE)
   json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
   open(p, "a", encoding="utf-8").write("\n")
   ```
4. **Проверить.** Сгенерировать несколько раз, сверить ответ независимым расчётом,
   убедиться, что нет `{...}` в тексте и типы ответа верны.
5. **Ворклист.** В `data/source_index/per_task_template_worklist.json` у задач листа
   проставить `template_text`, `number_strategy`, `answer_formula`, `answer_type`,
   `notes` (какой runtime-шаблон) и `status = "done"`.
6. **Тесты.** `python -m unittest discover -s tests` — должно быть зелёно, включая
   `test_no_template_is_fragile_across_seeds` (страж хрупкости).

## Команды проверки

```bash
# одна задача
python scripts/generate_problem_from_template.py --module compare_products --difficulty 6
# пересборка ворклиста (идемпотентна, не трогает status != todo)
python scripts/build_per_task_template_worklist.py
# весь тестовый набор
python -m unittest discover -s tests
```

## Definition of Done для темы

- заглушки листа удалены, вместо них авторский(е) шаблон(ы);
- генерация даёт задачи того же типа, что примеры корпуса листа;
- ответы сверены независимым расчётом; типы (`number/multi/text`) корректны;
- шаблон стабилен на многих сидах (страж-тест зелёный);
- задачи листа в ворклисте помечены `done` с ссылкой на runtime-шаблон;
- обновлён `Docs/WORK_LOG.md`.
