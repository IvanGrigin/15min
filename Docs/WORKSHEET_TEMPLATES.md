# Worksheet Templates

Этот документ описывает JSON-шаблоны листов с задачами и универсальный рендер.

## Где лежат шаблоны

- `data/templates/worksheets/`

Текущий готовый шаблон:

- `data/templates/worksheets/worksheet_5_tasks.json`

Готовый пример заполнения:

- `outputs/generated/worksheet_5_math_problems_example.json`

## Что описывает JSON-шаблон

Шаблон хранит только оформление и расположение элементов:

- размер страницы;
- фон и отступы;
- линии заголовка;
- поля `Фамилия`, `Имя`, дата;
- список слотов задач;
- правую панель под картинку и QR-код;
- плейсхолдеры вида `{{date}}`, `{{logo_path}}`, `{{qr_path}}`, `{{problems[0]}}`.

Шаблон не хранит:

- генерацию задач;
- вычисление ответов;
- бизнес-логику доменов.

## Как устроен шаблон `worksheet_5_tasks.json`

Главные блоки:

- `page` — размеры страницы и фон;
- `assets` — пути к логотипу и QR-коду, включая дефолтные файлы;
- `styles` — базовые размеры шрифтов и линии;
- `header` — верхние подписи `Фамилия`, `Имя`, две пустые линии для ручного заполнения и дата;
- `problem_area` — список слотов задач;
- `right_panel` — вертикальный блок для изображения и QR-кода;
- `placeholders` — декларативный список ожидаемых плейсхолдеров.

Каждый слот задачи содержит:

- `index`
- `text`
- `x`
- `y`
- `width`
- `height`
- `separator_y`

## Как подключить шаблон к задачам

Ручной запуск:

```bash
python scripts/render_worksheet.py --template data/templates/worksheets/worksheet_5_tasks.json --problems outputs/generated/counting.json --output outputs/generated/worksheet.pdf
```

Пример с уже подготовленными 5 арифметическими задачами:

```bash
python scripts/render_worksheet.py --template data/templates/worksheets/worksheet_5_tasks.json --problems outputs/generated/worksheet_5_math_problems_example.json --output outputs/generated/worksheet_example.pdf
```

Дополнительные опции:

- `--date`
- `--logo-path`
- `--qr-path`

Если `--logo-path` и `--qr-path` не переданы, рендерер берет дефолтные пути из блока `assets.defaults` шаблона.

## Какие входные JSON поддерживаются

Рендерер понимает два формата:

1. Bundle модульной архитектуры:
   - объект с полем `problems`;
   - текст берется из `problem_text`.

2. Простой список:
   - список объектов;
   - текст берется из `condition`, `problem_text` или `text`.

Для student JSON листа можно также передать:

- `header.date`
- `header.logo_path`
- `header.qr_path`

## Как добавить новый шаблон

1. Создать новый JSON в `data/templates/worksheets/`.
2. Описать страницу, `assets`, `header`, problem slots и боковые элементы.
3. Убедиться, что число слотов совпадает с числом задач, которые вы хотите рендерить.
4. При необходимости добавить новый пример запуска в документацию.

## Почему фамилия и имя пустые

В ученическом листе фамилия и имя не подставляются программой.

На листе должны быть:

- подпись `Фамилия`
- пустая линия после нее
- подпись `Имя`
- пустая линия после нее

Это нужно, чтобы ученик заполнял их вручную.

## Как заменить логотип и QR-код

Есть два способа:

1. Заменить файлы:
   - `assets/logo.png`
   - `assets/qr.png`

2. Или передать другие пути:
   - через `header.logo_path` / `header.qr_path` в JSON задач;
   - через `--logo-path` и `--qr-path` в CLI.

## Как работает рендер

Код лежит в:

- `problemgen/io/worksheet_renderer.py`

Он:

- загружает шаблон;
- проверяет число задач;
- перенумеровывает задачи;
- переносит текст по строкам внутри ширины блока;
- выдает понятную ошибку, если слот переполнен;
- сохраняет итог в `PDF` или `PNG`.
