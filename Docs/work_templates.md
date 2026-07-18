# Работа, производительность и совместные действия

Модуль `work_productivity_and_joint_actions` покрывает 16 deduplicated-источников
четырьмя exact-integer семействами: распилы, расход, равные расчёты и совместная
производительность. Каталог находится в `data/templates/problem_sets/work_productivity_and_joint_actions/`,
логика — в `problemgen/generation/work_templates.py`. Имена берутся из одной
approved-вселенной и остаются в безопасном именительном падеже.

Проверки: `py -3 -m unittest tests.test_work_templates` и
`py -3 scripts/validate_work_templates.py`.
