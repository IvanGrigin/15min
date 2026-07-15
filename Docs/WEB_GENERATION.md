# Web Generation

Этот документ описывает локальный сайт для генерации ученических листов.

## Что делает сайт

Сайт показывает 5 блоков выбора темы и сложности.

Для каждой задачи пользователь выбирает русскую тему из нового дерева и уровень от 1 до 10.

После нажатия на кнопку:

- backend проверяет входной JSON;
- выбирает только статические JSON-шаблоны подходящего модуля;
- генерирует переменные и ответы отдельно от текста;
- сохраняет student JSON и answers JSON;
- рендерит PDF-лист через `worksheet_5_tasks.json`;
- отдает ссылку на скачивание.

## Как запустить сайт

Из корня `15min`:

```bash
python scripts/run_site.py
```

Или с указанием адреса:

```bash
python scripts/run_site.py --host 127.0.0.1 --port 8090
```

После запуска сайт открывается по адресу:

```text
http://127.0.0.1:8090
```

## Как запустить генерацию без сайта

```bash
python scripts/generate_worksheet.py --items '[{"module":"tree_expression_value","difficulty":5},{"module":"tree_ages","difficulty":4},{"module":"tree_contains_digit_count","difficulty":6},{"module":"tree_area_scaling","difficulty":7},{"module":"tree_movement","difficulty":6}]'
```

## Как выбрать темы и сложности

На странице есть 5 карточек:

- Задача 1
- Задача 2
- Задача 3
- Задача 4
- Задача 5

В каждой карточке есть поле темы и поле сложности от 1 до 10. Доступные темы
сайт получает из `data/templates/problem_templates.json`, но показывает только
100 тем нового дерева `tree_*`. Пользователь видит русские названия веток:
`Арифметика и выражения`, `Алгебраические модели`, `Комбинаторика`,
`Движение и скорости` и т. д.

Технические `module`-идентификаторы остаются внутри HTML/API, потому что именно
по ним backend вызывает генератор. В интерфейсе вместо них отображаются русские
темы вида `A01 · Вычисление длинного выражения`.

Frontend отключает недоступные значения сложности для выбранной темы и показывает
превью пяти выбранных задач перед генерацией.

## Как создается лист

1. Frontend отправляет `POST /generate`.
2. Backend валидирует `items`: ровно пять объектов с `module` и `difficulty`.
3. `problemgen/worksheet/service.py` вызывает генератор статичных шаблонов.
4. Student JSON сохраняется в `outputs/generated/worksheet_problems_<timestamp>.json`.
5. Ответы сохраняются в `outputs/generated/worksheet_answers_<timestamp>.json`.
6. PDF сохраняется в `outputs/generated/worksheet_<timestamp>.pdf`.

Если для выбранной пары `module` + `difficulty` нет подходящего статичного шаблона,
backend возвращает ошибку до рендера листа.

## Где лежат файлы

- PDF: `outputs/generated/worksheet_<timestamp>.pdf`
- student JSON: `outputs/generated/worksheet_problems_<timestamp>.json`
- answers JSON: `outputs/generated/worksheet_answers_<timestamp>.json`

## Как связаны сайт, генератор задач и шаблон

- `frontend/worksheet_site.js` собирает 5 пар темы и сложности;
- `problemgen/web/worksheet_site.py` принимает запрос;
- `problemgen/web/worksheet_site.py` переводит `tree_*` модули в русские названия
  для страницы и `GET /api/modules`;
- `problemgen/worksheet/service.py` вызывает `problemgen/generation/template_generator.py`;
- `data/templates/problem_templates.json` хранит только математические текстовые шаблоны;
- `problemgen/io/worksheet_renderer.py` подставляет задачи в JSON-шаблон листа;
- `data/templates/worksheets/worksheet_5_tasks.json` отвечает только за внешний вид.

## Пример ответа backend

```json
{
  "ok": true,
  "worksheet_file": "worksheet_20260712_201607.pdf",
  "download_url": "/download/worksheet_20260712_201607.pdf",
  "answers_file": "worksheet_answers_20260712_201607.json"
}
```

## Пример запроса к backend

```json
{
  "items": [
    {"module": "tree_expression_value", "difficulty": 5},
    {"module": "tree_ages", "difficulty": 4},
    {"module": "tree_contains_digit_count", "difficulty": 6},
    {"module": "tree_area_scaling", "difficulty": 7},
    {"module": "tree_movement", "difficulty": 6}
  ]
}
```
