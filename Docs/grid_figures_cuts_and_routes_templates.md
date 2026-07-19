# Модуль 25: клетчатые фигуры, разрезания и маршруты

Используются два read-only корпуса `docs/25_*`. Из 31 уникального источника
19 покрыты пятью exact-integer семействами: перегородки с дырками, квадраты в
решётке, буква П, обратная задача по перегородкам и BFS-маршрут жука. Остальные
12 имеют неединственный, конструктивный, yes/no или diagram-dependent ответ.

Проверки: `py -3 -m unittest tests.test_grid_templates tests.test_worksheet_site`
и `py -3 scripts/validate_grid_templates.py`.
