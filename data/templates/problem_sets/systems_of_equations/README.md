# Problem set: Systems of Equations

Этот каталог хранит шаблоны для модуля `systems_of_equations`.

## Источник

Шаблоны построены только по файлу:

`docs/03_sistemy_uravneniy_updated.md`

В источнике 8 задач. Задачи `700` и `886` являются точными дубликатами, поэтому они записаны в один шаблон.

## Основной файл

`templates.json` содержит 7 уникальных структур систем уравнений.

Каждый шаблон хранит:

- `source_problem_numbers` — номера исходных задач;
- `source_examples` — исходные примеры;
- `coefficient_structure` — правила генерации коэффициентов;
- `generation_strategy` — способ построения системы.

## Проверка

```powershell
py -3 .\scripts\validate_system_equation_templates.py
py -3 -m unittest tests.test_system_equation_templates
```
