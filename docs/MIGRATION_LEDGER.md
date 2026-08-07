# Журнал переноса задач в JSON-шаблоны

Правила ведения — `docs/AGENT_TASK_TO_TEMPLATE_PROMPT.md`.
Одна строка = одна исходная задача корпуса. Статусы: `перенесена`, `отклонена`.

## Перенесено

| Задачи корпуса | template_id | Модуль | Доля удачных | Тест |
|----------------|-------------|--------|--------------|------|
| 8 | `motion_half_path_half_time_ride` | motion_speed_and_distance | 6 % | `tests/test_template_studio_morphology.py` |
| 8 (усложнение) | `motion_third_path_third_time_ride` | motion_speed_and_distance | 6 % | `tests/test_template_studio_morphology.py` |
| 110, 115 | `money_equalize_pair` | money_purchases_prices_and_calculations | 100 % | `tests/test_template_studio_money.py` |
| 161, 238 | `coin_ratio_three_people` | money_purchases_prices_and_calculations | 15 % | `tests/test_template_studio_money.py` |
| 100, 105, 1212 | `joint_payment_settlement` | work_productivity_and_joint_actions | 23 % | `tests/test_template_studio_work.py` |
| 208, 226, 1271 | `joint_work_rate_sum` | work_productivity_and_joint_actions | 8 % | `tests/test_template_studio_work.py` |
| 203, 221 | `process_circle_overlay` | number_processes_and_repeated_operations | 100 % | `tests/test_template_studio_process.py` |
| 380, 398 | `process_triangular_sum_next` | number_processes_and_repeated_operations | 100 % | `tests/test_template_studio_process.py` |
| 1204 | `process_states_merge_countdown` | number_processes_and_repeated_operations | 91 % | `tests/test_template_studio_process.py` |
| 36, 833, 1042 | `friends_periodic_meeting_lcm` | calendar_and_weekdays | 42 % | `tests/test_template_studio_calendar.py` |
| 307, 325 | `tram_interval_change` | calendar_and_weekdays | 11 % | `tests/test_template_studio_calendar.py` |
| 305, 323 | `school_day_short_break` | calendar_and_weekdays | 77 % | `tests/test_template_studio_calendar.py` |
| 198, 216, 1268 | `weekday_lesson_last_visit` | calendar_and_weekdays | 62 % | `tests/test_template_studio_calendar.py` |

Один шаблон `coin_ratio_three_people` закрывает обе задачи 161 и 238 разом: направление
отношения («в K раз меньше» / «в K раз больше») — параметр `relation`, а не два разных
шаблона, потому что математика внутри действительно разная (см. `math_notes` в файле).

Батч `calendar_and_weekdays` (2026-07-27), 10 задач → 4 шаблона:

- `tram_interval_change` (307, 325) — известный дефект источника (см. раздел
  «Известные дефекты исходных задач»): время оборота круга названо «длиной
  маршрута». В тексте шаблона это исправлено — говорится о времени оборота.
- `school_day_short_break` (305, 323) — источник даёт абсолютные часы прихода
  и ухода («в 8:55», «в 20:00»), которые математически избыточны (сама задача
  уже даёт `before`/`after` как относительные числа минут, часы нужны только
  чтобы получить общий бюджет времени). Движок не умеет форматировать время
  вида `Ч:ММ`, а вводить это ради одной задачи запрещено — заменено прямой
  фразой «всего от прихода до ухода проходит N минут», арифметика не меняется.
- **Правки после проверки человеком.** `tram_interval_change`: параметр `action`
  переключал только глагол, а предлог оставался общий — 72 % вариантов выходили
  с «на маршрут убрали» вместо «с маршрута убрали». Теперь `choice` несёт всю
  управляемую группу целиком. Там же убрана бессмысленная вставка «на весь круг
  у них в сумме уходило одно и то же время» и добавлен потолок интервала:
  32 минуты между трамваями формально верны, но неправдоподобны.
  `school_day_short_break`: свободные `integer` в роли минут давали «уходит через
  267 минут» и 12 часов в школе — заменены на `choice` с круглыми значениями.
  Обе ошибки прошли валидатор: он проверяет самосогласованность, а не смысл.
- `weekday_lesson_last_visit` (198, 216, 1268) — 1268 дословно повторяет 198
  (добавлен год «2025» в вопрос, на математику не влияет), 216 — тот же приём
  с другими числами; перенесены одним шаблоном. Отдельная грамматическая
  ловушка: месяц в ответе-дате не согласуется по счёту (1/2-4/5+), у дат он
  всегда в родительном падеже единственного числа — поэтому `answer_rendering`
  не использует `unit`/`unit_param`, ответ — голое число дня (подробности в
  `math_notes.grammar_trap` шаблона).

| 66, 85, 429, 447 | `drifting_watches_same_time` | clocks_dials_and_electronic_displays | 22 % | `tests/test_template_studio_clocks.py` |
| 310, 328 | `routine_sign_true_hours` | clocks_dials_and_electronic_displays | 91 % | `tests/test_template_studio_clocks.py` |
| 274, 292 | `tower_clocks_meet` | clocks_dials_and_electronic_displays | 59 % | `tests/test_template_studio_clocks.py` |
| 1158 | `cuckoo_full_turns` | clocks_dials_and_electronic_displays | 100 % | `tests/test_template_studio_clocks.py` |
| 181, 186, 674, 848, 986, 1001, 1144, 1152 | `tournament_round_robin_games` | sets_clubs_acquaintances_and_tournaments | 100 % | `tests/test_templates_sets_and_tournaments.py` |
| 1097, 1183, 1258 | `tournament_knockout_games` | sets_clubs_acquaintances_and_tournaments | 83 % | `tests/test_templates_sets_and_tournaments.py` |
| 465, 484, 569 | `tournament_boards_total_time` | sets_clubs_acquaintances_and_tournaments | 91 % | `tests/test_templates_sets_and_tournaments.py` |
| 669, 1262 | `two_languages_inclusion_exclusion` | sets_clubs_acquaintances_and_tournaments | 17 % | `tests/test_templates_sets_and_tournaments.py` |
| 194 | `class_friendship_bipartite` | sets_clubs_acquaintances_and_tournaments | 13 % | `tests/test_templates_sets_and_tournaments.py` |
| 392, 410 | `handshakes_between_two_grades` | sets_clubs_acquaintances_and_tournaments | 14 % | `tests/test_templates_sets_and_tournaments.py` |
| 175, 975, 1100 | `two_clubs_one_shared_girl` | sets_clubs_acquaintances_and_tournaments | 59 % | `tests/test_templates_sets_and_tournaments.py` |
| 247, 265 | `mixed_tournament_win_difference` | sets_clubs_acquaintances_and_tournaments | 16 % | `tests/test_templates_sets_and_tournaments.py` |
| 1116 | `coffee_with_milk_shares` | sets_clubs_acquaintances_and_tournaments | 100 % | `tests/test_templates_sets_and_tournaments.py` |
| 580, 598 | `heads_and_legs_two_species` | heads_legs_wheels_and_object_counts | 91 % | `tests/test_templates_heads_and_legs.py` |
| 5, 586, 1006, 1058, 1091 | `caravan_dwarves_and_pack_animals` | heads_legs_wheels_and_object_counts | 38 % | `tests/test_templates_heads_and_legs.py` |
| 180, 185, 188, 193, 389, 407, 985, 990, 995, 1000, 1073, 1084 | `hypnotist_false_animal_reports` | heads_legs_wheels_and_object_counts | 91 % | `tests/test_templates_heads_and_legs.py` |
| 579 | `box_of_bugs_and_spiders` | heads_legs_wheels_and_object_counts | 77 % | `tests/test_templates_heads_and_legs.py` |
| 583, 584 | `equal_legs_two_species` | heads_legs_wheels_and_object_counts | 100 % | `tests/test_templates_heads_and_legs.py` |
| 578 | `bicycles_two_and_three_wheels` | heads_legs_wheels_and_object_counts | 100 % | `tests/test_templates_heads_and_legs.py` |
| 582 | `treats_shared_unique_split` | heads_legs_wheels_and_object_counts | 27 % | `tests/test_templates_heads_and_legs.py` |
| 634 | `insects_in_the_room_chain` | heads_legs_wheels_and_object_counts | 24 % | `tests/test_templates_heads_and_legs.py` |
| 637 | `reserve_predators_and_herbivores` | heads_legs_wheels_and_object_counts | 56 % | `tests/test_templates_heads_and_legs.py` |
| 91, 96, 267, 285, 1137, 1250, 1450 | `friends_sum_of_ages_count` | ages_and_generations | 83 % | `tests/test_templates_ages_and_equations.py` |
| 771 | `two_ages_sum_and_difference` | ages_and_generations | 71 % | `tests/test_templates_ages_and_equations.py` |
| 1104 | `age_puzzle_as_old_as_now` | ages_and_generations | 100 % | `tests/test_templates_ages_and_equations.py` |
| 530 | `queue_of_three_generations` | ages_and_generations | 100 % | `tests/test_templates_ages_and_equations.py` |
| 518 | `queue_three_rounds_of_insertions` | word_problems_for_equation_setup | 100 % | `tests/test_templates_ages_and_equations.py` |
| 555, 556, 557, 558, 559, 560, 561, 1128, 1525 | `words_ratio_and_difference` | word_problems_for_equation_setup | 100 % | `tests/test_templates_ages_and_equations.py` |
| 14, 1079 | `trees_ratio_and_sum` | word_problems_for_equation_setup | 100 % | `tests/test_templates_ages_and_equations.py` |
| 166, 171, 842, 941 | `sausage_two_bites_leftover` | word_problems_for_equation_setup | 100 % | `tests/test_templates_ages_and_equations.py` |
| 493 | `candies_two_kinds_of_eaters` | word_problems_for_equation_setup | 71 % | `tests/test_templates_ages_and_equations.py` |
| 498 | `guessed_number_reverse_chain` | word_problems_for_equation_setup | 14 % | `tests/test_templates_ages_and_equations.py` |
| 593 | `pills_descending_by_one` | word_problems_for_equation_setup | 100 % | `tests/test_templates_ages_and_equations.py` |
| 1127 | `buns_between_boys_and_girls` | word_problems_for_equation_setup | 83 % | `tests/test_templates_ages_and_equations.py` |
| 710 | `weekly_growing_tasks` | word_problems_for_equation_setup | 100 % | `tests/test_templates_ages_and_equations.py` |
| 777 | `chipmunks_equal_target` | word_problems_for_equation_setup | 77 % | `tests/test_templates_ages_and_equations.py` |
| 89, 94, 98, 103, 889, 894, 1135, 1210, 1335, 1410 | `count_parity_in_range` | integer_interval_counting | 62 % | `tests/test_templates_counting_and_sequences.py` |
| 664 | `count_integers_strictly_between` | integer_interval_counting | 100 % | `tests/test_templates_counting_and_sequences.py` |
| 25, 139, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 937, 1175 | `count_multiples_in_range` | divisibility_multiples_remainders_primes | 67 % | `tests/test_templates_counting_and_sequences.py` |
| 41 | `count_even_multiples_in_range` | divisibility_multiples_remainders_primes | 62 % | `tests/test_templates_counting_and_sequences.py` |
| 534 | `remainder_by_two_signs` | divisibility_multiples_remainders_primes | 56 % | `tests/test_templates_counting_and_sequences.py` |
| 1142 | `digits_all_from_one_set` | digits_number_notation_and_cryptarithms | 100 % | `tests/test_templates_counting_and_sequences.py` |
| 44, 1051, 1067, 1396 | влит в `arithmetic_series_sum_plain` (был `arithmetic_progression_sum`) | arithmetic | 100 % | `tests/test_templates_equations_and_arithmetic.py` |
| 179, 184, 192, 353, 372, 382, 400, 979, 984, 989, 994 | `consecutive_numbers_digit_count` | sequences_progressions_and_sums | 71 % | `tests/test_templates_counting_and_sequences.py` |
| 1076 | `alternating_double_and_subtract` | sequences_progressions_and_sums | 91 % | `tests/test_templates_counting_and_sequences.py` |
| 773, 1313 | `count_numbers_by_length` | digits_number_notation_and_cryptarithms | 100 % | `tests/test_templates_digits.py` |
| 814, 1198, 1313 | `count_numbers_first_last_classes` | digits_number_notation_and_cryptarithms | 100 % | `tests/test_templates_digits.py` |
| 818 | `count_numbers_without_digit` | digits_number_notation_and_cryptarithms | 100 % | `tests/test_templates_digits.py` |
| 815, 1143 | `count_numbers_fixed_middle_digit` | digits_number_notation_and_cryptarithms | 100 % | `tests/test_templates_digits.py` |
| 8, 13, 18, 21, 1078 | `digit_occurrences_in_range` | digits_number_notation_and_cryptarithms | 62 % | `tests/test_templates_digits.py` |
| 812, 860, 868, 1032, 1047, 1139, 1314 | `permutations_of_repeated_digits` | digits_number_notation_and_cryptarithms | 100 % | `tests/test_templates_digits.py` |
| 29, 42, 1064 | `numbers_with_small_digit_sum` | digits_number_notation_and_cryptarithms | 91 % | `tests/test_templates_digits.py` |
| 107, 112, 1227 | `last_digit_of_product_plus` | digits_number_notation_and_cryptarithms | 83 % | `tests/test_templates_digits.py` |
| 236, 254 | `uphill_and_back_distance` | motion_speed_and_distance | 34 % | `tests/test_templates_motion.py` |
| 63, 82, 427, 445 | `competition_three_legs` | motion_speed_and_distance | 15 % | `tests/test_templates_motion.py` |
| 309, 327 | `two_drivers_before_meeting` | motion_speed_and_distance | 71 % | `tests/test_templates_motion.py` |
| 352, 371 | `dog_runs_there_and_back` | motion_speed_and_distance | 24 % | `tests/test_templates_motion.py` |
| 283, 301 | `elevator_ride_time` | motion_speed_and_distance | 21 % | `tests/test_templates_motion.py` |
| 56, 75, 420, 438 | `three_walkers_catch_up` | motion_speed_and_distance | 36 % | `tests/test_templates_motion.py` |
| 340, 359, 383, 401, 414, 432 | `equation_multiply_add_divide` | equations | 18 % | `tests/test_templates_equations_and_arithmetic.py` |
| 7, 12, 196, 214 | `equation_divide_by_unknown` | equations | 100 % | `tests/test_templates_equations_and_arithmetic.py` |
| 120, 130 | `equation_two_level_nesting` | equations | 91 % | `tests/test_templates_equations_and_arithmetic.py` |
| 233, 251 | `equation_sum_divide_subtract` | equations | 100 % | `tests/test_templates_equations_and_arithmetic.py` |
| 17, 20 | `equation_subtract_bracket_product` | equations | 24 % | `tests/test_templates_equations_and_arithmetic.py` |
| 594, 1123, 1124, 1261, 1323, 1324, 1461, 1522, 1524 | `common_factor_two_products` | arithmetic | 67 % | `tests/test_templates_equations_and_arithmetic.py` |
| 87, 92, 1133, 1333 | `three_near_multipliers` | arithmetic | 36 % | `tests/test_templates_equations_and_arithmetic.py` |
| 544-549, 825-827, 1108, 1118, 1125, 1226, 1426, 1523 | `arithmetic_series_sum_plain` | arithmetic | 83 % | `tests/test_templates_equations_and_arithmetic.py` |
| 1196, 1231, 1245, 1431, 1445 | `alternating_series_sum` | arithmetic | 91 % | `tests/test_templates_equations_and_arithmetic.py` |
| 343, 362 | `nuts_on_distinct_plates` | ratios_fractions_proportions_and_percentages | 100 % | `tests/test_templates_equations_and_arithmetic.py` |
| 272, 290, 1107 | `three_shares_candies` | ratios_fractions_proportions_and_percentages | 37 % | `tests/test_templates_equations_and_arithmetic.py` |
| 517, 1221 | `doubling_reaches_half` | ratios_fractions_proportions_and_percentages | 100 % | `tests/test_templates_equations_and_arithmetic.py` |
| 1191 | `three_boxes_mutual_difference` | ratios_fractions_proportions_and_percentages | 83 % | `tests/test_templates_equations_and_arithmetic.py` |

### Батч 4: модуль 16 «Часы и табло»

25 задач корпуса: 9 перенесено четырьмя шаблонами, 16 отклонено. Такая доля
отклонений здесь закономерна: больше половины темы — задачи про электронное
табло вида «когда в k-й раз все цифры станут разными», а это перебор секунд,
для которого `solver_strategy: formula` не подходит по определению.

Два дефекта из аудита учтены до написания текста:
- **«первые/вторые часы»** — в источнике непонятно, чьи именно часы имеются
  в виду. В шаблоне у каждых часов назван владелец: «часы Вани», «часы Димы».
  Проверяется тестом `test_owner_named_for_each_watch`.
- **сравнение по модулю 1440** (MAT-006) — старый генератор искал первое
  совпадение без него. В `math_notes` это записано явно, чтобы следующий агент
  не «упростил» до 720.

Задача 1158 упрощена намеренно: исходное начальное время 12:05 на ответ
не влияет, и его наличие создаёт ложное ощущение, будто его надо учитывать.

### Батч 5: модуль 23 «Множества, клубы, знакомства и турниры»

26 задач корпуса: 23 перенесено девятью шаблонами, 3 отклонено. Доля переноса
здесь заметно выше, чем в «Часах», потому что тема почти целиком состоит
из задач-близнецов: восемь формулировок кругового турнира отличались только
числом участников и числом кругов.

Исправлен дефект источника (задачи 465, 484, 569). В условии шесть игроков
играют «сразу на двух полях» круговой турнир из 15 партий. Такого расписания
не существует: 15 партий не раскладываются на туры по две, и объявленное время
недостижимо. В шаблоне досок ровно n/2 при чётном n — тогда круговой турнир
честно разбивается на n−1 туров, и условие перестаёт быть выдумкой.
Тест `BoardsTotalTimeTests` строит расписание методом карусели и проверяет,
что каждый тур действительно заполняет все доски.

Два замечания по русскому, найденных чтением выдачи, а не тестом:
- «собрал 31 человек» — винительный одушевлённого при числительном на 1
  требует «31 человека», а счётный слот такой формы не даёт. Числа,
  оканчивающиеся на 1, исключены constraint'ом и проверяются тестом.
- «4 мальчиков и 6 девочек» — числа участников обязаны идти счётным слотом.
  Первая редакция подставляла их обычным числом и ломала согласование.

### Батч 6: модуль 22 «Головы, ноги, колёса и подсчёт объектов»

29 задач корпуса: 26 перенесено девятью шаблонами, 3 отклонено. Двенадцать
задач про гипнотизёра оказались одним шаблоном: менялись только заявленные
числа голов и ног.

Тема потребовала одной общей возможности движка — признака у существительного.
Число ног живого существа не написано в условии: ученик знает его из жизни.
Если бы шаблон писал «у курицы 2 ноги» текстом, первая же подстановка коровы
сделала бы условие ложным. Теперь legs лежит в словаре рядом со словом,
а тип параметра `noun_trait` подаёт его в формулу.

Из того же принципа выросли теги. Без них гипнотизёр опрашивал в деревне
тигров, а гномы навьючивали поклажу на комаров: пул «любое двуногое»
слишком широк. Тег farm выделяет двор и ферму, insect — коробку с жуками,
pack — вьючных животных. Чтобы добавить верблюда, достаточно тега.

Отдельно стоит отметить, чего проверка НЕ ловит. Все девять шаблонов прошли
валидацию с первого раза, и все девять были испорчены по-русски: «12 пар пар»,
«каждый из уток», «73 колёс», «голов оказалось 69 голов». Это нашлось только
чтением десяти примеров глазами — шаг, который в алгоритме стоит после
валидации именно поэтому.

### Батч 7: модули 21 «Возраст и поколения» и 31 «Задачи на составление уравнений»

32 задачи корпуса, все перенесены четырнадцатью шаблонами. Модуль 21 оказался
слишком тонким для отдельного батча — 11 задач, из которых часть лежит там
по ошибке разметки, — поэтому добран соседний модуль 31, как и предписывают
правила. Вместе они дали две крупные группы близнецов: семь задач про сумму
возрастов и девять про «знает в k раз больше слов».

Два места, где чтение выдачи поймало ложь, которую валидация пропустила:
- «Мама Свинка старше, чем бабушка Свинка, на 14 лет» — арифметика верна,
  утверждение ложно. Возрастные шаблоны переведены на обычные имена, как
  и в источнике.
- «Задумал число, ... вышло 2. Ответ: 2» — цепочка вернула задуманное число,
  и задача решается, не считая. Закрыто ограничением и отдельным тестом.

Задача 777 про бурундуков потребовала обратной параметризации от цели: если
разыгрывать запасённое напрямую, условие «осталось запасти вчетверо больше»
почти никогда не выполняется в целых числах.

### Батч 8: промежутки, делимость, цифры и прогрессии

45 задач корпуса, перенесено девятью шаблонами. Открыты четыре новые темы;
две из них закрыты почти целиком: «Подсчёт целых чисел в промежутках» (11 задач
из 14) и «Делимость» (16 из 23).

**Перенос из архива.** Впервые взято не условие, а математика из
заархивированных Python-генераторов. Оттуда пришли две вещи, каждая из которых
и есть вся трудность своей темы:

- обработка границ промежутка: `high//d - (low-1)//d` для замкнутого
  и `(high-1)//d - low//d` для открытого. В архиве это была функция `_count`
  с флагом `open_`, здесь — две ветки одного выражения и `choice` на тип границ;
- «чётное и кратное d» считается через НОК, а не умножением на два: при чётном
  делителе шаг совпал бы с самим делителем. Constraint оставляет только
  нечётные делители, чтобы задача не вырождалась.

Сам архивный код переносить нельзя и не нужно: там текст условия в f-строках,
имена в одну букву и `str()` внутри формул. Ценна была только выверенная
арифметика границ.

**Дефект, найденный тестом на единственность.** «Выписали 603 подряд идущих
числа, всего 1809 цифр» — все числа трёхзначные, и первое не восстанавливается:
подходит любое начало от 100 до 397. Отрезок обязан пересекать разрядную
границу, иначе число цифр не зависит от начала. Закрыто constraint'ом
и отдельным тестом.

**Задача 534 переформулирована.** В источнике «делится ли число на 12» —
ответ да/нет с обоснованием. Спрашивается остаток: ответ стал числом, а смысл
сохранился, потому что делители взаимно просты и остаток по произведению
восстанавливается по двум признакам. Тест проверяет это перебором по китайской
теореме об остатках.

### Батч 9: цифры и запись чисел

Тема была открыта одним шаблоном из 129 задач — теперь их девять, перенесено
23 задачи. Крупные группы близнецов: семь задач на перестановки цифр и пять
на подсчёт вхождений цифры в записи чисел отрезка.

**Я вписал в math_notes выдуманные контрольные числа и был пойман тестом.**
Для задачи «сколько раз цифра 2 встречается в числах от 1 до 120» я записал
ответ 32, не считая. Перебор дал 23. Проверены и исправлены все контрольные
значения батча; каждое теперь подтверждено перебором. Урок общий: строка
«контроль по источнику» в math_notes обязана быть посчитана, а не оценена
на глаз — иначе она хуже, чем её отсутствие, потому что выглядит проверкой.

Проверка формул устроена в два этапа, потому что полный перебор возможен
не везде: до четырёх-пяти разрядов тест строит все числа и смотрит на них
строками, дальше сверяет формулу с независимо написанной динамикой по разрядам.

Отклонена большая группа — около двадцати задач вида «сколько чисел
в промежутке содержат цифру d». У них нет закрытой формы при произвольных
границах, только перебор.

### Батч 10: движение, скорость и расстояние

Шесть шаблонов, 16 задач. Тема была самой недобранной из открытых: два шаблона
на 60 задач. Слой способов передвижения пригодился сразу — в задаче про подъём
в гору глагол и единица скорости берутся из профиля героя, поэтому пешеход
идёт километрами, а корабль плывёт узлами; в задаче про две встречные машины
оба участника обязаны быть на колёсах, и скорости приходят из их диапазона.

**Тест поймал вырожденную систему.** В задаче про лифт два известных времени
дают систему на скорость лифта и время остановки. При top−1 = 3·(mid2−1)
уравнения пропорциональны, система вырождается, и ответ перестаёт быть
единственным: перебор нашёл пять разных ответов на одно условие. Закрыто
явным условием ненулевого определителя.

**Снова наступил на ловушку из этого же журнала.** В задаче про троих пешеходов
я поставил ограничение «третий быстрее второго», а деление на разность
скоростей стоит в derived_values — они считаются раньше проверок, и падение
случалось до запрета. Разность сделана положительной по построению.

**Параметр, живущий только в ответе, движок считает неиспользованным** — и он
прав: ученик такого слова не видит. Единицу расстояния пришлось вынести
в вопрос: «Сколько километров от подножия до вершины?» вместо «Какое
расстояние». Это касается трёх шаблонов батча.

### Батч 11: уравнения, арифметика, доли и проценты

Тринадцать шаблонов, 47 задач, три новые темы. Персонажи здесь почти не нужны:
это упражнения на счёт и на порядок действий, а не сюжеты.

**Уравнения проверяются подстановкой, а не пересчётом.** Тест берёт числа
из готового текста, собирает левую часть заново по порядку действий
и сравнивает с правой. Так проверяется и ответ, и сам текст: если бы шаблон
напечатал не то число, подстановка не сошлась бы. Отдельная проверка следит,
что ни одно деление в цепочке не даёт остатка.

**Арифметические приёмы проверяются их отсутствием.** Вынесение общего
множителя и группировку соседних множимых тест не применяет — он умножает
и складывает в лоб. Совпадение и означает, что приём законен.

**Круглая сумма задана конструкцией.** В двух шаблонах требование «сумма
множителей кратна десяти» сначала стояло отсевом и оставляло 10 % наборов.
Переписано так, что второй множитель считается из круглой суммы: стало 67 %
и 36 %.

**Я ослабил чужую проверку под свой шаблон и откатил это.** Задача про орехи
на тарелках начиналась с числа, а инвариант сайта требует заглавной буквы
в начале. Вместо того чтобы переписать условие, я сначала разрешил в своём
тесте цифру в начале — то есть сделал ровно то, что запрещает правило №4.
Проверка возвращена строгой, условие переписано: «На столе 23 жёлудя. Их
разложили…».

### Батч 12: все модули и расширение уже подключённых

15 шаблонов корпуса закрыли все 31 допустимый `module_id` активного каталога.
Два первых (`system_sum_and_difference` и `symmetric_products_difference`)
были подготовлены до начала батча в текущей ветке; остальные тринадцать добавлены
в JSON-библиотеку вместе с независимым решателем `tests/test_templates_missing_modules.py`.
Полная публикация проверила каждый из 105 активных шаблонов на десяти сидах.

| Задачи корпуса | template_id | Модуль | Тест |
|----------------|-------------|--------|------|
| 570, 571, 573, 630, 631, 700, 703, 886 | `system_sum_and_difference` | systems_of_equations | `tests/test_templates_equations_and_arithmetic.py` |
| 570, 571, 573, 630, 631, 700, 703, 886 | `system_two_linear_equations` | systems_of_equations | `tests/test_templates_equations_and_arithmetic.py` |
| 88, 93, 97, 102, 1134, 1184, 1209 | `symmetric_products_difference` | comparison_of_numbers_and_expressions | `tests/test_templates_equations_and_arithmetic.py` |
| 306, 324, 368, 1020, 1025 | `crossed_products_difference` | comparison_of_numbers_and_expressions | `tests/test_templates_equations_and_arithmetic.py` |
| 1138 | `factorial_value` | factors_products_and_factorials | `tests/test_templates_missing_modules.py` |
| 418, 436, 451, 470 | `count_odd_open_interval` | combinatorics_and_counting_variants | `tests/test_templates_missing_modules.py` |
| 492 | `balls_guaranteed_two_black` | pigeonhole_and_guaranteed_selection | `tests/test_templates_missing_modules.py` |
| 52, 71, 416, 434, 819 | `uniform_numbers_parity_sum` | parity_invariants_strategies_and_moves | `tests/test_templates_missing_modules.py` |
| 90, 95 | `square_area_from_perimeter` | plane_geometry_rectangles_squares_and_areas | `tests/test_templates_missing_modules.py` |
| 99, 1211 | `grid_square_count` | grid_figures_cuts_and_routes | `tests/test_templates_missing_modules.py` |
| 32, 123, 133, 1038, 1063, 1267 | `cube_paint_surface_scaling` | cubes_volume_and_spatial_geometry | `tests/test_templates_missing_modules.py` |
| 673, 934, 939, 1283 | `line_uniform_points_distance` | points_segments_and_positions_on_a_line | `tests/test_templates_missing_modules.py` |
| 126, 909 | `container_weight_with_quarter` | quantities_units_weight_and_scaling | `tests/test_templates_missing_modules.py` |
| 35, 1153 | `alphabet_permutation_position` | alphabetic_order | `tests/test_templates_missing_modules.py` |
| 64, 83, 428, 446, 835 | `wrong_product_correction` | logic_problems_and_condition_analysis | `tests/test_templates_missing_modules.py` |

Проверка по смыслу обнаружила и исправила ошибку до публикации: для ветки
«третье слово ИАВН» 22-м словом является «НВАИ», а не «НАВИ». Независимый
тест перебирает все 24 возможных алфавита и все перестановки, поэтому не
повторяет условную строку JSON. В логической задаче имена учеников берутся
из пула и оба глагола согласуются по роду; в первой версии чтение примеров
поймало «Аня должен был».

### Батч 13: множители, произведения и факториалы

Весь активный исторический модуль из семи записей разобран в
`data/template_studio/legacy_migration/factors_products_and_factorials.json`:
у каждой записи есть исходный strategy, номера задач, итоговый JSON, статус
миграции и результат проверки. Четыре варианта минимума суммы множителей
объединены в один шаблон с параметром вида множителей; это именно
структурные дубликаты, а не четыре конкурирующие реализации.

| Задачи корпуса | template_id | Модуль | Тест |
|----------------|-------------|--------|------|
| 33, 46, 122, 127, 137, 141, 145, 150, 165, 930, 935, 940, 950, 999, 1053, 1266, 1284 | `factor_pair_min_sum` | factors_products_and_factorials | `tests/test_templates_factors.py` |
| 118, 132, 925 | `factor_pair_min_sum_without_zero_digits` | factors_products_and_factorials | `tests/test_templates_factors.py` |
| 1199 | `trailing_zeros_consecutive_product` | factors_products_and_factorials | `tests/test_templates_factors.py` |

Независимые тесты перебирают делители для задач о минимальной сумме, а число
нулей получают прямым перемножением всей напечатанной последовательности.
Так они не повторяют формулы JSON. Просмотр десяти вариантов для каждого
нового шаблона выполнен до публикации.

### Батч 14: алфавитный порядок

Полная матрица пяти активных legacy-записей находится в
`data/template_studio/legacy_migration/alphabetic_order.json`. Добавлены
четыре отсутствующих операции со скрытым алфавитом: следующее, предыдущее и
первое слово из перестановок, а также возможное последнее слово при
повторах. Для уже существовавшего поиска позиции добавлена вся исходная
атрибуция.

| Задачи корпуса | template_id | Тест |
|----------------|-------------|------|
| 35, 864, 1057, 1153, 1172 | `alphabet_permutation_position` | `tests/test_templates_alphabet.py` |
| 40, 466, 485, 865, 1070 | `alphabet_permutation_next` | `tests/test_templates_alphabet.py` |
| 863 | `alphabet_permutation_previous` | `tests/test_templates_alphabet.py` |
| 862 | `alphabet_permutation_first` | `tests/test_templates_alphabet.py` |
| 1071 | `alphabet_repetition_last` | `tests/test_templates_alphabet.py` |

Тест перебирает все 24 возможных порядка букв, восстанавливает порядок по
напечатанной подсказке и только затем получает ответ. Для последнего слова с
повторениями он проверяет существование ответа, так как слово на пятой
позиции намеренно не определяет весь скрытый алфавит.

### Инвентаризация: чётность и инварианты

Единственная активная запись исторического модуля полностью соответствует
`uniform_numbers_parity_sum`; в
`data/template_studio/legacy_migration/parity_invariants_strategies_and_moves.json`
зафиксировано сопоставление и добавлены все номера её исходных задач.

### Инвентаризация: головы, ноги, колёса и объекты

Три широкие записи архивного генератора отражены в
`data/template_studio/legacy_migration/heads_legs_wheels_and_object_counts.json`.
Они уже были разложены на конкретные JSON-типы с независимыми проверками,
поэтому новые конкурирующие шаблоны не создавались. Непереносимые номера
581, 585 и 1177 остаются явно учтёнными в разделе «Отклонено».

## Отклонено

| Задача | Тема | Причина | Комментарий |
|--------|------|---------|-------------|
| 202 | number_processes | `search_answer` | Последовательность Коллатца: «через сколько минут впервые получится число меньше X». Число шагов не выражается формулой — только итерацией, а `safe_expressions` не знает циклов (и это его осознанное свойство, а не пробел). Кандидат на отдельное обсуждение: понадобился бы примитив ограниченной итерации в движке — решение уровня архитектуры, а не батча. |
| 220 | number_processes | `search_answer` | Та же задача Коллатца с другими числами (46, порог 20). |
| 1182 | number_processes | `duplicate` | Дословный повтор задачи 202 (70, порог 10) с более подробным пересказом примера. |
| 19, 22, 62, 81, 280, 298, 426, 444, 830, 1317 | clocks | `search_answer` | «В какое время в k-й раз все цифры на табло будут различными» — требуется перебор секунд суток, закрытой формы нет. Десять задач одной структуры. |
| 350, 369, 388, 406 | clocks | `search_answer` | «Когда впервые пять из шести цифр окажутся одинаковыми» — тот же перебор. |
| 1161 | clocks | `structured_answer` | «Сможет ли повернуть циферблат…» — ответ да/нет с обоснованием, а не число. |
| 3, 30, 136, 157, 174, 199, 217, 268, 286, 363, 654-663, 707, 1061, 1234, 1235 | digits | `search_answer` | «Сколько чисел в промежутке содержат (или не содержат) цифру d» — при произвольных границах закрытой формы нет, только перебор. Около двадцати задач одной структуры. |
| 51, 70, 821 | digits | `needs_new_slot` | Криптарифмы со звёздочками: нужен решатель столбиком, которого у движка нет. |
| 57, 76, 421, 439, 838, 1022 | digits | `structured_answer` | «Придумайте три числа с суммой S» — ответ из трёх чисел. |
| 347, 366, 386, 404 | digits | `search_answer` | Восстановление четырёхзначного числа по сумме с усечённым: требуется перебор вариантов. |
| 47, 1054, 1060 | intervals | `search_answer` | «Сколько нечётных чисел от 100 до 1000 содержит хотя бы одну цифру 3» — требуется перебор чисел, закрытой формы нет. |
| 540, 543 | divisibility | `structured_answer` | Задачи на доказательство: «докажите, что B равно только 1, 3 или 9». |
| 638 | divisibility | `search_answer` | Наименьшее шестизначное число по трём условиям на цифры — перебор. |
| 348, 367, 387, 405 | sequences | `search_answer` | Цифра на 2021-м месте в рекуррентной последовательности: нужен проход по периоду. |
| 496 | sequences | `non_parametric` | Сумма девяти циклических перестановок 123456789: держится на конкретном числе. |
| 1102 | sets | `non_parametric` | Пять команд, известны очки четырёх. Задача держится на конкретных числах 1, 2, 5, 7: сумма очков в турнире зависит от числа ничьих, и однозначность возникает только при этом наборе. Свободных параметров нет. |
| 1086 | equations | `structured_answer` | Двенадцатый вагон и девятый с конца — соседние. Подходят и 19 вагонов, и 21: ответ из двух чисел. |
| 504 | equations | `structured_answer` | «Не ошибся ли пастух?» — ответ да/нет с обоснованием через инвариант. |
| 581 | heads_legs | `needs_new_slot` | Дроиды и клоны генерала: две части тела сразу (ноги и руки). Нужен второй числовой признак `arms` рядом с `legs`. Признак симметричен уже имеющемуся, но заполнять его есть чем лишь у нескольких слов — заводить полупустую колонку ради одной задачи преждевременно. |
| 1177 | heads_legs | `corrupt_source` | Лило и Стич считают пальцы после клонирования. Сколько пальцев на руке у Стича и сколько рук было изначально, в условии не сказано, а ответ от этого зависит. |
| 585 | heads_legs | `search_answer` | Тридцатичетырёхножки и драконы: число ног дракона восстанавливается перебором допустимых пар, а не формулой. |
| 781 | ages | `non_parametric` | «Сколько прабабушек и прадедушек было у всех ваших прабабушек и прадедушек» — обыгрывается одно конкретное слово, менять нечего. |
| 1166 | clocks | `non_parametric` | Часы идут назад, сколько раз в сутки покажут верное время. Свободных чисел нет: ответ 4 при любой формулировке, менять нечего. |

## В очереди (не отклонены, требуют отдельного разбора в следующем батче)

| Задачи | Тема | Почему не в этом батче |
|--------|------|------------------------|
| 743 | work | тот же сюжет, что и 208/226, но с дополнительным вопросом «а если делится?» — другая математика (объединение труда), отдельный шаблон |
| 780 | work | классическая «пять рыбаков — пять судаков» — единичная, не близнец в этом файле |
| 1110 | work | 48 кузнецов/60 лошадей — оптимизация с целочисленными ограничениями («лошадь не может стоять на двух ногах»), нужно проверить, формула ли это или перебор |
| 1155 | work | сближение/расхождение по прямой — похоже на чистую формулу, отложено по времени |
| 1188 | work | воробьи и зёрна — двойное неравенство, решение через целочисленные границы, отдельный разбор |
| 1194 | work | сравнение удоев коров — система уравнений с выводом знака неравенства, а не числа — вероятно `structured_answer` |
| 156 | money | поиск/перечисление монет по условию — вероятно `search_answer`, требует отдельного разбора |
| 201, 219 | money | сбор подарка вскладчину — не близнецы (разное число участников с известными взносами), нужен отдельный формульный разбор |
| 210, 228, 744 | money | минимизация стоимости по двум размерам упаковки — не выражается одной формулой (нужен перебор комбинаций); кандидат на добавление обобщённой функции в `safe_expressions`, а не per-task Python |
| 235, 253 | money | восстановление порядка цен из равенства сумм — решается, но не делалось в этом батче |
| 313, 331 | money | распределение долга за подарок из двух частей — близнецы, отложено |
| 349, 368 | money | мороженое / кратность «во сколько раз больше» — отложено |
| 351, 370, 801 | money | оптимизация номеров в отеле — похоже на закрытую форму (сравнение выручки на м²), но нужно доказать формулой без перебора; отложено |
| 356, 375 | money | долевая покупка ноутбука с амортизацией — отложено |
| 394, 412 | money | обмен валюты с одинаковой комиссией — похоже на «результат не зависит от индивидуальной суммы», перспективный шаблон; отложено |
| 10 | equations | три блюда и две группы едоков: система 2x2 и вопрос про третью величину — структурно как гипнотизёр, но отдельный сюжет; отложено |
| 239 | equations | лишний ноль в конце второго слагаемого — разбор через разряды, отдельный шаблон |
| 778 | equations | горшочки Винни-Пуха: ответ — перечисление возможных домиков, нужно проверить, единственный ли |
| 1103, 1187, 1202 | equations | номера вагонов, квартир и парт — задачи на согласование двух нумераций; отдельный разбор |
| 490, 525, 528 | money | единичные сюжетные задачи без явных близнецов — по одной, отложено |

## Известные дефекты исходных задач

Найдены внешним аудитом 1000 задач (ветка `codex/russian-text-migration`).
Учитывать при переносе соответствующей задачи — полный разбор
в `docs/HARVEST_FROM_LEGACY_AUDIT.md`.

| Задачи | Дефект |
|--------|--------|
| 307, 325 (трамваи) | в исходной формулировке время прохождения круга названо длиной маршрута |
| движение, знакопеременное смещение | ответ ошибочно умножался на 60 |
| часовые пояса | остаток по модулю 24 часа терял день прибытия |
| чётность | текст и решение использовали разные предикаты |
| муха между пешеходами | целочисленное деление обрезало ответ |
| встречные поезда | длины поездов принудительно равны половинам |

## Данные

| Дата | Что добавлено |
|------|---------------|
| 2026-07-26 | существительные «сектор», «круг», «государство» |
| 2026-07-26 | 29 слов через конвейер правил (`docs/DATA_PIPELINE.md`): парта, тетрадь, портфель, автобус, остановка, магазин, продавец, покупатель, коробка, пакет, бутылка, стакан, ложка, стул, стол, окно, дверь, ступенька, лифт, замок, грядка, помидор, огурец, капуста, велосипедист, пешеход, водитель, пассажир, билетик. Словарь: 258 слов |
| 2026-07-26 | **исправлено 15 дефектов в старом словаре**, найденных сверкой с правилами склонения: у 11 слов nom_pl был скопирован из род. ед. ч. («грамма» вместо «граммы»); у «человек» три падежа мн. ч. были забиты счётной формой вместо «люди/людей»; у «голова» и «нога» винительный мн. не соответствовал неодушевлённости. Класс ошибок закрыт тестом `tests/test_noun_dictionary_integrity.py` |
| 2026-07-26 | **канон закрыт целиком**: 132 персонажа с падежами добрано до всех 25 вселенных × 6 = 150. Имена сверены с `docs/approved_dimensions_150_characters.md` тестом |
| 2026-07-26 | новый файл `data/entities/characters/extended_characters.json` — 102 персонажа 17 миров за пределами канона: Гравити Фолз, Мифы Древней Греции, Герои Древней Греции, Русские народные сказки, Сказки Пушкина, Бременские музыканты, Ёжик в тумане, Щенячий патруль, Свинка Пеппа, Русалочка, Аладдин, Микки Маус и друзья, Тачки, Сказки Андерсена, Сказки Шарля Перро и братьев Гримм, Робин Гуд, Король Артур |
| 2026-07-26 | новый файл `data/entities/universes.json` — 42 вселенные, 84 локации с полной падежной парадигмой и предлогом, 210 предметов, разложенные по 9 группам миров |
| 2026-07-26 | 88 новых существительных (предметы вселенных); 9 вещественных помечены `countable: false` |
| 2026-07-25 | 18 персонажей франшиз: Властелин колец, Смешарики, Простоквашино (по 6) |
| 2026-07-25 | существительные «километр», «раз» (с переопределением форм счёта), «викторина», «задача» |
| 2026-07-25 | новый пул `data/entities/characters/common_names.json` — 19 обычных русских имён (Вася, Петя, Надя, Оля, Аня, Дима, Марк, Алина, Кирилл, Серёжа, Гриша, Ралина, Максим, Илья, Миша, Саша, Коля, Паша, Вадим) с полными падежами. Архитектурное уточнение: в отличие от 25 франшизных вселенных, этот пул не сверяется с `docs/approved_dimensions_150_characters.md` — он существует отдельно, потому что большинство текстовых задач корпуса (деньги, доли, возраст) используют обычные имена детей, а не персонажей франшиз. Загрузчик `problemgen/russian/characters.py` объединяет оба источника в одном реестре под sentinel-вселенной `COMMON_POOL = "Обычные имена"`. |

## Разбор замечаний преподавателя (2026-08-07)

`docs/REVIEW_BACKLOG.md` разобран целиком: все 55 замечаний закрыты.
Отдельными строками — то, что вышло за пределы правки одного шаблона:

- `arithmetic_progression_sum` перестал существовать как отдельная запись:
  после снятия подсказки он отличался от `arithmetic_series_sum_plain`
  только героем, то есть был оболочкой. Влит туда `story_variant`-ом,
  тема больше не занимает отдельную категорию.
- `count_odd_open_interval` вобрал подсчёт чётных чисел в промежутке:
  приём тот же, разыгрывается остаток.
- Обитатели двадцати вселенных были записаны словом «житель». Заменены
  на своё для каждого мира: жевуны, коротышки, дачники, атланты, шахтёры,
  трубочисты, дровосеки. В словарь добавлено 15 существительных;
  у «осла», «коротышки» и «дровосека» правило склонения ошибается,
  их формы заданы явно.
- В решателе `caravan_dwarves_and_pack_animals` найдена ошибка, которую
  не ловил ни один тест: подстрока «на ос» — родительный множественного
  осы — находится внутри «на ослов», и вьючному животному приписывалось
  шесть ног. Поиск переведён на границы слова.
- Изменений в Python ради конкретных задач по-прежнему нет: всё, кроме
  тестов-решателей, сделано данными.

## Новые приёмы: кубики, вагоны, цепочка цифр (2026-08-07)

| номера | шаблон | модуль | тест |
|---|---|---|---|
| 146, 234, 252, 460, 479, 1093 (всего 17 задач группы) | `cube_painted_faces` | cubes_volume_and_spatial_geometry | `tests/test_templates_geometry_and_pigeonhole.py` |
| 284, 302 | `train_cars_common_divisor` | word_problems_for_equation_setup | `tests/test_templates_missing_modules.py` |
| 348, 367, 387, 405 | `last_digit_recurrence` | sequences_progressions_and_sums | `tests/test_templates_counting_and_sequences.py` |

Отклонено:

- `equal_money_transfer` — **duplicate**. План покрытия числил задачи 110 и 115
  непокрытыми, но их уже печатает `money_equalize_pair`, и притом лучше:
  там валюта берётся из вселенной, а не зашита рублями. Шаблон был написан
  и удалён; проверка `tests/test_source_references.py` поймала совпадение
  раньше, чем он попал в каталог.
- `digits_in_range` (26 задач в каталоге непокрытого) — покрыто шаблоном
  `count_in_range_by_digit`. Каталог непокрытого на этом месте устарел.

Изменения в Python на уровне движка: одно — тип параметра `digit_recurrence`
и решатель `problemgen/template_studio/digit_recurrence.py`. Цепочка, где
каждая цифра равна последней цифре произведения или суммы двух предыдущих,
требует памяти о виденных парах и поиска периода; ни цикла, ни словаря
в языке выражений нет. Устроено так же, как `alphabet_order.py` и
`digit_predicates.py`: Python проходит цепочку, JSON называет действие
(«произведения», «суммы»), длину показанного начала и место вопроса.
Изменений в Python ради конкретной задачи нет.

## Батч «прямоугольники и меры» (2026-08-07)

| номера | шаблон | модуль | тест |
|---|---|---|---|
| 39, 314, 332, 874, 1045, 1056, 1081 | `rectangle_perimeter_exceeds_area` | plane_geometry_rectangles_squares_and_areas | `tests/test_templates_rectangles_and_measures.py` |
| 183, 983 | `square_side_from_area_growth` | plane_geometry_rectangles_squares_and_areas | там же |
| 453, 472, 799 | `rectangle_cut_and_glue_to_square` | plane_geometry_rectangles_squares_and_areas | там же |
| 151, 671 | `rectangle_side_from_area_mixed_units` | plane_geometry_rectangles_squares_and_areas | там же |
| 670 | `square_with_same_perimeter` | plane_geometry_rectangles_squares_and_areas | там же |
| 170, 970 | условие `one_square` в готовом `factor_pair_min_sum` | multipliers_products_and_factorials | `tests/test_templates_factors.py` |

Три задачи корпуса из этого батча просят «приведите пример», и кажется,
что примеров много. Их по одному: у «периметр на 2023 больше площади»
из (x−2)(y−2) = 4 − gap следует, что меньшая сторона равна единице;
у «отрезать и приклеить до квадрата» периметр отрезаемой полосы равен
удвоенной большей стороне, потому что меньшая в нём сокращается. Поэтому
ответ печатается целиком, обеими сторонами, и тесты требуют единственности
перебором — иначе ребёнок с верным вторым примером получил бы крестик.

Отклонено:

- «Представьте 575 в виде произведения нескольких чисел с суммой 37» (597) —
  **structured_answer**: число сомножителей там не задано, и набор не с чем
  сверять даже по свойству.

Отклонение снято:

- «Придумайте четыре числа с суммой 173, произведение которых кончается шестью
  нулями» (209, 227, 342, 361) сперва были отклонены как `structured_answer`.
  Отклонение неверно: источник прямо пишет «достаточно привести всего один
  пример», то есть подходит любой верный ответ. Сделан шаблон
  `numbers_with_sum_and_zero_product`, где ключ печатает пример и говорит
  об этом словами, а проверка идёт по свойству набора, а не по совпадению
  с образцом.
- «Попытайтесь получить N, перемножая два сомножителя, один из которых
  нечётный» (33, 46, 122, 127, 137, 141, 165, 930, 935, 940, 999, 1053, 1266,
  1284) — **duplicate**: условие `one_odd` в `factor_pair_min_sum` уже есть,
  и шаблон это печатает. План батча числил их непокрытыми ошибочно.

Изменений в Python на уровне движка нет: добавлено одно условие отбора
(`one_square`) в существующий решатель `factor_pairs.py`. Изменений ради
конкретной задачи нет.

## Наборы чисел с нулями в произведении (2026-08-07)

| номера | шаблон | модуль | тест |
|---|---|---|---|
| 209, 227, 342, 361 | `numbers_with_sum_and_zero_product` | factors_products_and_factorials | `tests/test_templates_factors.py` |

Изменения в Python на уровне движка: два.

1. Тип параметра `zero_product_set` и решатель
   `problemgen/template_studio/zero_product_sets.py`. Набор собирается
   конструктивно: нужные двойки и пятёрки раскладываются по числам, сумма
   считается по набору. Свободного числа в наборе нет — при сумме 83
   и четырёх нулях все три числа обязаны нести множители, как в решении
   корпуса 50 + 8 + 25.
2. Формат ответа `example_of_many` в `render_answer`. Нужен там, где верных
   ответов много, а источник просит один пример: ключ печатает «например:
   10, 20, 50 (подойдёт любой набор…)». Прежде у движка было только `any_of`,
   который перечисляет все варианты, — здесь их сотни. Пояснение приходит
   из данных полем `note`, потому что зависит от задачи, а не от движка.

Изменений в Python ради конкретной задачи нет.

## Сводка

- Шаблонов в библиотеке: 144
- Вселенных с падежами, локациями, предметами и ценностями: 43
- Персонажей с падежами: 252 франшизных + 19 обычных имён
- Существительных с полной парадигмой: 439
- Изменений в Python ради конкретных задач: нет
- Изменений в Python на уровне движка (общая возможность, не логика задачи): две —
  1. `problemgen/russian/characters.py` — объединение персонажей франшиз и пула
     обычных имён в один реестр по полю `pool`;
  2. `problemgen/russian/universes.py` (новый) — загрузчик вселенных: локации
     с падежами и предлогом, предметы мира, группы миров;
  3. тип параметра `location` и `from_universe_items` в `runtime.py` — локация
     и предмет берутся из вселенной, к которой уже привязаны персонажи;
  4. слоты `{place:loc}` / `{place:dir}` (где/куда) и `{hero:with}` (с/со) —
     выбор предлога зависит от случайно выбранного слова, поэтому его нельзя
     оставлять автору шаблона;
  5. флаг `countable` у существительного — запрет считать вещественные слова;
  6. `problemgen/template_studio/runtime.py: render_answer` — добавлен `unit_param`
     (единица измерения в ответе берётся из значения параметра-существительного,
     а не только из фиксированной леммы); понадобилось, когда `joint_work_rate_sum`
     выбирает случайно между «олимпиада» и «викторина» — ответ обязан согласоваться
     именно с тем словом, что попало в текст, а не с захардкоженной леммой.
