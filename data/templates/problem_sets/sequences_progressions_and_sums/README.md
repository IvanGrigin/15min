# Набор шаблонов «Последовательности, прогрессии и суммы»

`templates.json` объединяет структуры из двух read-only источников: задач без
персонажей и задач с персонажами. Повторяющиеся номера источника объединены в
один шаблон, поэтому не влияют на вероятность выбора.

Генератор: `problemgen/generation/sequence_templates.py`.

Проверка:

```powershell
py -3 .\scripts\validate_sequence_templates.py
py -3 -m unittest tests.test_sequence_templates
```
