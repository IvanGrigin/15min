# Семейства шаблонов

Единая анатомия тематического набора `data/templates/problem_sets/<id>/`:
`templates.json` + README, генератор `problemgen/generation/<id>_templates.py`,
валидатор `scripts/validate_<id>_templates.py`, тесты `tests/test_<id>_templates.py`,
конспект в `Docs/`. Сайт собирает лист из выбранных модулей.

Правило: записи с `active: false` нужны для полного учёта исходников
(source accounting) и сайтом не выбираются — не удалять и не «чинить».
