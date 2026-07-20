# problemgen/web

Здесь лежит локальный HTTP-слой.

Он должен:

- пользоваться уже готовыми сервисами каталога и генерации;
- не дублировать доменную логику;
- не хранить словари сущностей;
- уметь показывать итоговый JSON и trace-данные.

`worksheet_site.py` также отдаёт локальный административный маршрут
`/admin/template-studio`. Он использует `problemgen/template_studio/` для
черновиков, проверок и active overlay, а не содержит анализатор или вычислитель
формул внутри HTTP-handler.

`/admin/template-creator` — provider-backed маршрут автоматического JSON;
секреты читаются только в `problemgen/template_creator` из окружения.
