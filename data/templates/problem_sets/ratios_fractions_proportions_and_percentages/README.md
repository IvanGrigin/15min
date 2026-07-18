# Отношения, доли, пропорции и проценты

Набор параметрических шаблонов модуля
`ratios_fractions_proportions_and_percentages`. Источники — два read-only файла
`docs/10_..._deduplicated.md`; 26 уникальных задач учитываются ровно один раз в
`source_accounting.json`.

`templates.json` содержит только runtime-шаблоны с целым ответом. Генератор
строит связанные величины от заранее выбранного целого решения и повторно
проверяет ответ независимым решателем.

Проверка:

```powershell
py -3 scripts/validate_ratio_templates.py
py -3 -m unittest tests.test_ratio_templates
```
