# Большая задача: довести покрытие корпуса до 90%

## Счёт

Мера — `tools/coverage_report.py` (близость по основам слов, повторы схлопнуты).

* различных задач в корпусе — **683**
* было на старте плана — 455 (66.6%)
* стало — **477 (69.8%)**
* цель 90% — **615**, то есть осталось закрыть **ещё 138** из 206

Наблюдаемая скорость: один шаблон закрывает в среднем **1,6 задачи**
(14 шаблонов дали 22 задачи). Значит до 90% нужно ещё около **85 шаблонов**,
и это не оценка «на глаз», а прямой счёт по сделанному. Планировать
следующие волны надо из этого числа, а не из желаемого.

Это значит, что почти всё непокрытое должно получить шаблон. Отсюда порядок
работы: идти не «по интересным задачам», а по семьям, вычищая тему целиком.

## Правила, которые не меняются

* Независимый решатель в тестах — решает задачу заново по напечатанному
  тексту и другим способом.
* Условие не подсказывает решение.
* Ответ единственный; если приём допускает несколько — печатаются все.
* Одинаковая математика с разным сюжетом — **варианты одного шаблона**.
* **Перед новым шаблоном ищите номер задачи в `source_metadata` уже
  существующих.** Дважды за прошлую волну заготовка оказывалась повтором.
* Ни строчки условия в Python: текст в JSON, Python только решает.

---

## Что сделано

| шаблон | закрыл |
|---|---|
| `two_kinds_count_by_traits` — система по двум признакам | 581, 585 |
| `circular_track_meetings` — сумма скоростей к разности | 1167 |
| `forgot_item_return_point` — возвращение стоит удвоенного | 1156 |
| `lake_with_spring_elephants` — озеро с родником | 722 |
| `position_from_both_ends` — двойной счёт предмета | 487 |
| `logs_equal_cuts` — распилов на единицу меньше частей | 275 |
| `vitamin_course_bounds` — три вилки перемножаются | 228 |
| `watermelon_drying_percent` — считать сухую часть | 1190 |
| `bridge_over_river_length` — доля моста над водой | 1260 |
| `square_units_conversion` — квадрат отношения | 713 |
| `boxes_growing_row_sum` — сумма 1 + 2 + … + n | 1098 |
| `minimal_group_by_percent` — доля одного человека | 1192 |
| `apples_boxes_and_shares` — доли от разного | 635 |
| `traveler_four_days_backwards` — обратный ход | 521 |
| `trucks_for_warehouse_load` — округление вверх | 839 |

Появился `tools/claimed_tasks.py`. Пользуйтесь им **до** написания шаблона:
за две волны четыре заготовки оказались повторами существующих (турнир
каждый с каждым, турнир на выбывание, время на досках, передача денег
поровну) — все удалены до публикации.

## Что осталось: семьи, которым нужен решатель

Это самое дорогое и самое ценное из оставшегося — приёмы, которых
в движке ещё нет:

| семья | задачи | почему нужен решатель |
|---|---|---|
| `bushes_along_fence` | 119, 128, 1249 | инвариант по остаткам и чётности |
| `epidemic_growth_days` | 304, 322 | половинки до нуля, шаг за шагом |
| `three_months_ninety_days` | 308, 326 | перебор троек месяцев с високосным |
| `palindrome_numbers` | 315, 333, 489 | поиск ближайшего палиндрома |
| `delete_digit_and_multiply` | 520, 526, 1218 | обратный перебор с вычёркиванием |
| `bug_diagonal_square` | 60, 424, 798, 1292 | ходы короля по клеткам |
| `same_birthday_weekday` | 346, 365 | календарь и високосные годы |
| `knights_and_knaves` | 508, 512, 513 | перебор природ участников |

## Волна 1. Семьи, где один шаблон закрывает пять и больше

| шаблон | приём | задачи | закроет |
|---|---|---|---|
| `legs_and_heads_mix` | сколько ног и голов у смеси существ | 581–585, 598, 1177 | 7 |
| `knights_and_knaves` | остров рыцарей и лжецов: опросы и заявления | 508, 512–514, 516 | 5 |
| `forgot_item_return` | вернулся за забытым — во сколько раз ускориться | 391, 409, 733, 750, 1156 | 5 |
| `round_robin_and_knockout` | турнир каждый с каждым и на выбывание | 465, 569, 1097, 1102, 1152 | 5 |
| `circular_track_meetings` | встречи на круге, смена направления | 459, 740, 1167, 1272 | 4 |

## Волна 2. Тройки

| шаблон | задачи | закроет |
|---|---|---|
| `vitamin_course_bounds` — границы курса «2–3 таблетки 3–5 раз в день» | 210, 228, 744 | 3 |
| `two_riders_meet` — встречное движение и возвращение | 758, 1155, 1170 | 3 |
| `average_speed_two_halves` — какая постоянная скорость равносильна | 751, 754, 1189 | 3 |
| `points_on_line_order` — точки на прямой и отрезки между ними | 121, 643, 1115 | 3 |
| `weight_comparison_chain` — цепочка «тяжелее — легче» | 786, 787, 1132 | 3 |
| `pies_divided_equally` — 7 пирогов на 8 детей | 847, 1312 | 2 |

## Волна 3. Пары — по две задачи на шаблон

`zigzag_speed_walk` (756, 757) · `snail_climb_tree` (523, 748) ·
`monkeys_eat_rate` (320, 338) · `letter_by_rider` (281, 299) ·
`mixed_up_order_price` (235, 253) · `ice_cream_shortfall` (349, 368) ·
`compare_bundles_price` (788, 789) · `gift_unknown_share` (201, 219) ·
`epidemic_growth_days` (304, 322) · `same_birthday_weekday` (346, 365) ·
`calculator_wrong_digit` (239, 257) · `bushes_along_fence` (119, 128, 1249) ·
`bug_diagonal_square` (60, 424, 798, 1292) · `palindrome_numbers` (315, 333, 489) ·
`delete_digit_and_multiply` (520, 526, 1218) · `three_months_ninety_days` (308, 326) ·
`logs_sawing_pieces` (275, 293) · `lake_with_spring` (722, 840) ·
`sets_intersection_min` (669, 1092) · `books_shelf_position` (487, 668, 1202) ·
`train_carriage_position` (1086, 1187)

## Волна 4. Одиночки, которые дёшевы при готовом приёме

`trains_pass_each_other` (495) · `walk_or_bus` (1169) · `speed_per_km_change` (1159) ·
`frogs_race` (1162) · `train_interval_count` (354) · `phone_and_case` (769) ·
`tea_price_bounds` (791) · `cow_trade_profit` (490) · `robbers_growing_coins` (1168) ·
`shop_pens_profit` (1259) · `three_pirates_redistribution` (527) ·
`who_solved_most` (1224) · `boat_three_fishermen` (1201) · `barefoot_boys` (1237) ·
`safe_code_digits` (537) · `two_carpets_overlap` (246) ·
`rectangle_with_two_holes` (1290) · `square_feet_inches` (713) ·
`watermelon_water_percent` (1190) · `bridge_parts_length` (1260) ·
`dried_fruit_yield` (639) · `boxes_total_weight` (839) ·
`traveler_fraction_path` (521) · `swan_and_geese` (529) · `min_people_percent` (1192) ·
`boxes_increasing_chocolate` (1098) · `lilies_doubling` (517) ·
`apples_two_bases` (635) · `albums_on_shelf` (1113) · `santa_circle_gifts` (319, 337)

## Как мерить продвижение

```
python3 tools/coverage_report.py
python3 tools/coverage_report.py --missing 20 --theme 18_dvizhenie
```

После каждой волны — полный прогон тестов, публикация и коммит.
