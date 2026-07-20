# `problemgen/template_studio`

Исполняемый слой локальной административной Template Studio.

- `analyzer.py` — прозрачные детерминированные эвристики исходного текста;
- `safe_expressions.py` — AST-вычислитель без `eval`;
- `runtime.py` — bounded sampling, derived-значения и рендер активной записи;
- `storage.py` — изолированное файловое хранилище и атомарный active overlay;
- `service.py` — статусы, аудит, preview, validation, activation и archive;
- `catalogue.py` — адаптер overlay-каталога к сайту.

Пакет не редактирует `data/templates/problem_sets/*`. Веб-слой
`problemgen/web/worksheet_site.py` вызывает только сервис и runtime-адаптер;
математика и безопасные выражения не дублируются в `frontend/`.
