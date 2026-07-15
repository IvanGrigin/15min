# Набор `arithmetic`

Назначение:

- хранит параметрические шаблоны по модулю `Арифметические вычисления`;
- используется последним сайтом для выбора ровно пяти шаблонов;
- источник математических структур: `docs/01_arifmeticheskie_vychisleniya_updated.md`.

Файлы:

- `templates.json` — рабочий каталог арифметических шаблонов;
- `README.md` — это описание.

Проверка:

```bash
python scripts/validate_arithmetic_templates.py
python -m unittest tests.test_arithmetic_templates
```

Важно:

- исходный Markdown не редактировать;
- новые арифметические шаблоны добавлять в `templates.json`;
- если появляется другой раздел математики, создать соседнюю папку в
  `data/templates/problem_sets/`, а не смешивать его с арифметикой.
