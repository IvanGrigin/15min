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
4. Использовать существующую `number_strategy` либо добавить общий алгоритм в `problemgen/generation/template_generator.py`.
5. Запустить `python -m unittest tests.test_template_generator`.

Новые сюжеты одного математического типа добавляются отдельными JSON-записями с той же математической стратегией, но другим `template_text`.

## Запуск одной задачи

```bash
python scripts/generate_problem_from_template.py --module joint_work --difficulty 4
```

Команда печатает JSON с `problem_text`, отдельным `answer` и фактическими `variables`.
