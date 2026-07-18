# Модуль 12: принцип Дирихле и гарантированный выбор

ID `pigeonhole_and_guaranteed_selection`. Два read-only источника содержат 6
уникальных задач после удаления 3 дублей из 9 записей. Три runtime-семейства
покрывают 5 источников: гарантию третьей категории после удаления первой,
восстановление трёхцветного инвентаря и минимальную выборку для нужного числа
целевых объектов. Задача 1150 исключена: у неё два вопроса и не заданы границы
парка, необходимые для гарантированного ответа.

Каталог и manifest: `data/templates/problem_sets/pigeonhole_and_guaranteed_selection/`.
Генератор: `problemgen/generation/pigeonhole_templates.py`. Параметры строятся
назад от согласованного худшего случая; минимум равен максимальному
неблагоприятному выбору плюс необходимое число целевых предметов. Активных
именованных источников нет, поэтому character binding и склонение не нужны.

Проверка: `py -3 scripts/validate_pigeonhole_templates.py` и
`py -3 -m unittest tests.test_pigeonhole_templates tests.test_worksheet_site`.
Для расширения нужны semantic ID, точная manifest-запись, независимый solver и
20+ fixed-seed проверок.
