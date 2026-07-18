# Модуль 15: календарь и дни недели

ID `calendar_and_weekdays`. Два read-only источника содержат 55 уникальных
задач после удаления 17 дублей. 35 источников активны в 10 exact-integer
семействах: ISO-коды дней недели, условные месяцы, максимум суммы цифр,
интервалы, смещения дат, отпуск, палиндромные даты, LCM-встречи, weekly schedule
и перемены. 20 источников исключены, поскольку требуют текста дня недели,
нескольких вариантов либо нескольких ответов.

Реальный григорианский календарь (`datetime.date`) учитывает високосные годы.
Именованные семейства используют approved-персонажей одной вселенной и оставляют
имя в именительном падеже. Каталог находится в
`data/templates/problem_sets/calendar_and_weekdays/`, генератор —
`problemgen/generation/calendar_templates.py`.

Проверка: `py -3 scripts/validate_calendar_templates.py` и
`py -3 -m unittest tests.test_calendar_templates tests.test_worksheet_site`.
