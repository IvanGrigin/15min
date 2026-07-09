# problemgen/io

Здесь должен жить слой чтения и записи.

## Примеры будущих функций

- `read_json_file()`
- `write_task_bundle()`
- `dump_task_instance()`
- `load_worksheet_template()`
- `render_worksheet()`

## Что уже есть сейчас

- `worksheet_renderer.py` — универсальная загрузка JSON-шаблона листа, проверка числа задач, перенос текста по строкам и рендер в `PDF` или `PNG`.
