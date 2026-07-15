# Problem set: Equations

Этот каталог хранит шаблоны для модуля `equations`.

## Источник

Шаблоны построены по файлу:

`docs/02_uravneniya_i_neravenstva_without_1502.md`

В источнике 160 задач. Номер `1502` намеренно отсутствует и не должен попадать в покрытие.

## Основной файл

`templates.json` содержит:

- одиночные уравнения;
- неравенства на наибольшее натуральное решение;
- системы линейных уравнений;
- составные задания с пунктами `а`, `б`, `в`.

Каждый шаблон хранит `source_problem_numbers`, чтобы было видно, из каких исходных задач он сделан.

## Пересборка

```powershell
py -3 .\scripts\build_equation_templates_from_source.py
```

## Проверка

```powershell
py -3 .\scripts\validate_equation_templates.py
py -3 .\scripts\validate_equation_templates.py --seeds 100
py -3 -m unittest tests.test_equation_templates
```
