# Web Generation

Этот документ описывает локальный сайт для генерации ученических листов.

## Что делает сайт

Сайт показывает 5 блоков выбора сложности.

Для каждой задачи пользователь выбирает уровень от 1 до 10.

После нажатия на кнопку:

- backend проверяет входной JSON;
- генерирует 5 задач через существующий арифметический генератор;
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
python scripts/generate_worksheet.py --difficulties 1,3,5,7,10
```

## Как выбрать сложности

На странице есть 5 selector-полей:

- Задача 1
- Задача 2
- Задача 3
- Задача 4
- Задача 5

Каждое поле принимает значение от 1 до 10.

## Как создается лист

1. Frontend отправляет `POST /generate`.
2. Backend валидирует `difficulties`.
3. `problemgen/worksheet/service.py` генерирует 5 задач.
4. Student JSON сохраняется в `outputs/generated/worksheet_problems_<timestamp>.json`.
5. Ответы сохраняются в `outputs/generated/worksheet_answers_<timestamp>.json`.
6. PDF сохраняется в `outputs/generated/worksheet_<timestamp>.pdf`.

## Где лежат файлы

- PDF: `outputs/generated/worksheet_<timestamp>.pdf`
- student JSON: `outputs/generated/worksheet_problems_<timestamp>.json`
- answers JSON: `outputs/generated/worksheet_answers_<timestamp>.json`

## Как связаны сайт, генератор задач и шаблон

- `frontend/worksheet_site.js` собирает 5 выбранных уровней;
- `problemgen/web/worksheet_site.py` принимает запрос;
- `problemgen/worksheet/service.py` вызывает существующие арифметические шаблоны;
- `problemgen/io/worksheet_renderer.py` подставляет задачи в JSON-шаблон листа;
- `data/templates/worksheets/worksheet_5_tasks.json` отвечает только за внешний вид.

## Пример запроса к backend

```json
{
  "difficulties": [1, 3, 5, 7, 10]
}
```
