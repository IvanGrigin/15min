# Problem set: Comparison of Numbers and Expressions

Этот каталог хранит шаблоны для модуля `comparison_of_numbers_and_expressions`.

## Источники

Математические структуры взяты только из файлов:

- `docs/04a_sravnenie_bez_imen_i_personazhey.md`
- `docs/04b_sravnenie_s_imenami_i_personazhami.md`

Персонажи и вселенные берутся только из файла:

- `docs/approved_dimensions_150_characters.md`

## Основной файл

`templates.json` содержит один общий пул шаблонов для задач с персонажами и без персонажей.

В модуле 14 уникальных шаблонов, которые покрывают 25 исходных номеров.

## Проверка

```powershell
py -3 .\scripts\validate_comparison_templates.py
py -3 -m unittest tests.test_comparison_templates
```
