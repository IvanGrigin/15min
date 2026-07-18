# Наборы шаблонов задач

Эта папка хранит тематические наборы шаблонов, которые могут использоваться
генератором и сайтом.

Каждый набор должен лежать в отдельной папке:

```text
data/templates/problem_sets/<id>/
  templates.json
  README.md
```

Рекомендуемый смысл файлов:

- `templates.json` — параметрические шаблоны задач;
- `README.md` — описание источника, структуры и команд проверки;
- исходные тексты задач лучше хранить в `docs/` или `Docs/source_documents/`, а
  в `templates.json` указывать путь к источнику через `source_file`.

Общий список доступных наборов хранится в `data/templates/problem_sets/catalog.json`.
Это позволяет позже добавить, например, `geometry`, `logic`, `movement` или
`combinatorics`, не смешивая их с арифметикой.

Сейчас подключены наборы:

- `arithmetic` — арифметические вычисления;
- `equations` — уравнения и неравенства;
- `systems_of_equations` — системы линейных уравнений с двумя переменными;
- `comparison_of_numbers_and_expressions` — сравнение чисел и выражений.
- `sequences_progressions_and_sums` — последовательности, прогрессии и суммы.
- `integer_interval_counting` — подсчёт целых чисел в промежутках.
- `divisibility_multiples_remainders_primes` — делимость, кратные, остатки и простые числа.
- `digits_number_notation_and_cryptarithms` — цифры, запись чисел и криптарифмы.
- `ratios_fractions_proportions_and_percentages` — отношения, доли, пропорции и проценты.
- `factors_products_and_factorials` — множители, произведения и факториалы.
- `combinatorics_and_counting_variants` — комбинаторика и подсчёт вариантов.
- `pigeonhole_and_guaranteed_selection` — принцип Дирихле и гарантированный выбор.
- `parity_invariants_strategies_and_moves` — чётность, инварианты, стратегии и ходы.
- `number_processes_and_repeated_operations` — числовые процессы и повторяющиеся операции.
- `calendar_and_weekdays` — календарь и дни недели.
- `clocks_dials_and_electronic_displays` — часы, циферблаты и электронные табло.
- `time_zones_and_travel_schedules` — часовые пояса и расписания поездок.
- `motion_speed_and_distance` — движение, скорость и расстояние.
