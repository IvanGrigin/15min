# Часовые пояса и расписания поездок

Модуль `time_zones_and_travel_schedules` использует 43 deduplicated-источника
из двух файлов модуля 17. 40 источников активны в шести integer-семействах:
локальная длительность, разворот, прямое прибытие, обратный маршрут и два
именованных маршрута. №636 и №747 исключены как чужие/multi-answer задачи,
№1316 — как yes/no-вопрос.

`problemgen/generation/time_zone_templates.py` хранит offsets в целых минутах,
переводит local time в абсолютную шкалу и обратно, явно применяя modulo суток.
Именованные маршруты используют одну approved-вселенную и безопасный
именительный падеж. Проверки: `py -3 -m unittest tests.test_time_zone_templates`
и `py -3 scripts/validate_time_zone_templates.py`.
