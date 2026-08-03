# Большая задача: довести покрытие корпуса до 90%

## Счёт

Мера — `tools/coverage_report.py` (близость по основам слов, повторы схлопнуты).

* различных задач в корпусе — **683**
* покрыто — **455 (66.6%)**
* цель 90% — **615**, то есть закрыть **ещё 160** из 228 оставшихся

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
