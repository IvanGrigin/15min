# Модуль 23: множества, клубы, знакомства и турниры

Каталог содержит восемь active exact-integer шаблонов и отдельный manifest
полного учёта 26 уникальных задач двух read-only источников. Четыре задачи с
несколькими или неединственными ответами не участвуют в runtime-выборе и имеют
точные причины исключения в `source_accounting.json`.

`templates.json` читает `problemgen/generation/sets_templates.py`; сайт
подключает его через `problemgen/web/worksheet_site.py`.
