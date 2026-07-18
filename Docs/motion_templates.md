# Движение, скорость и расстояние

Модуль `motion_speed_and_distance` учитывает 60 источников модуля 18: 45 active
и 15 multi-answer/text/yes-no или тематически чужих исключений. Шесть семейств
строят связанные целые величины для чередующегося движения, догонки,
многоэтапного пути, поездов, падения с палочки и мухи до встречи.

Генератор: `problemgen/generation/motion_templates.py`; catalog и manifest:
`data/templates/problem_sets/motion_speed_and_distance/`. Именованные задачи
берут distinct approved-персонажей одной вселенной и не склоняют имена
эвристикой. Проверки: `py -3 -m unittest tests.test_motion_templates` и
`py -3 scripts/validate_motion_templates.py`.
