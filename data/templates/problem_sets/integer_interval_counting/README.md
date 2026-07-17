# Набор шаблонов «Подсчёт целых чисел в промежутках»

`templates.json` содержит пять уникальных структур из read-only источника
`docs/06_podschet_tselyh_chisel_v_promezhutkah.md`. Дубликаты исходных номеров
собраны в одну запись и не влияют на вероятность выбора.

Проверка:

```powershell
py -3 .\scripts\validate_integer_interval_templates.py
py -3 -m unittest tests.test_integer_interval_templates
```
