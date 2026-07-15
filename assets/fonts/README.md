# Локальные шрифты листа

В папке лежат три начертания Lato 2.015: Regular, Bold и Black. Это полный
кириллический выпуск семейства под SIL Open Font License 1.1; текст лицензии
сохранён как `OFL.txt`.

`frontend/worksheet_site.css` подключает эти файлы через `@font-face`, а
`problemgen/web/worksheet_site.py` отдаёт их из `/assets/fonts/`. Поэтому
экранный предпросмотр и печать не зависят от Google Fonts или другого CDN.
