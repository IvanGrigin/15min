# Часы, циферблаты и электронные табло

`clocks_dials_and_electronic_displays` — модуль 16 с английским названием
`Clocks, Dials and Electronic Displays`.

Источники: `16_chasy_tsiferblaty_i_elektronnye_tablo_bez_imen_i_personazhey_deduplicated.md`
и `16_chasy_tsiferblaty_i_elektronnye_tablo_s_imenami_i_personazhami_deduplicated.md`.
Из 37 исходных записей после удаления 12 дублей осталось 25: 24 активны в семи
семействах, №1161 исключён как yes/no-вопрос.

Семейства: поиск состояний шестизначного электронного табло, ровно пяти равных
цифр, встреча правильных и обратных башенных часов, ход и отставание часов,
двухчастное суточное расписание, кукушка и обратный ход аналоговых стрелок.
Время моделируется целыми секундами или минутами modulo 24 часа; деления
принимаются только при точном результате.

Каталог лежит в `data/templates/problem_sets/clocks_dials_and_electronic_displays/`.
`problemgen/generation/clock_templates.py` загружает только active-записи,
проверяет manifest и независимо решает каждую конструкцию. Именованные задачи
выбирают distinct approved-персонажей одной вселенной; текст оставляет имена в
именительном падеже и не применяет эвристическое склонение.

Проверки: `py -3 -m unittest tests.test_clock_templates`,
`py -3 scripts/validate_clock_templates.py`, затем `py -3 -m unittest discover -s tests`.
Новый шаблон добавляют вместе с source-accounting, независимой сверкой и
регистрацией в `worksheet_site.py`.
