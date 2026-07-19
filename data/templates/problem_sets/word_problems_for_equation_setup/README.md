# Текстовые задачи на составление уравнений

Модуль 31 использует два read-only источника с 45 уникальными номерами после
удаления 12 дублей. Активные номера объединены в 10 exact-integer семейств;
остальные учтены с точной причиной в `source_accounting.json`.

Проверки: `py -3 -m unittest tests.test_equation_word_templates` и
`py -3 scripts/validate_equation_word_templates.py`.
