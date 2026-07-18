# Модуль 13: чётность, инварианты, стратегии и ходы

ID `parity_invariants_strategies_and_moves`. Из 31 исходной записи удалено 8
дублей; manifest учитывает 23 уникальные задачи. Один exact-integer шаблон
покрывает 11 источников: сумма элементов конечного списка по условию чётности
соседних цифр. Он поддерживает режимы «есть одинаковая чётность» и «все
соседние различны». Остальные 12 источников явно исключены как proof,
construction, yes/no или multi-answer; именованный источник 536 также yes/no.

Каталог: `data/templates/problem_sets/parity_invariants_strategies_and_moves/`;
генератор: `problemgen/generation/parity_templates.py`. Активных character-задач
нет, поэтому morphology не требуется. Fixed seed воспроизводим. Проверка:
`py -3 scripts/validate_parity_templates.py` и unit/site regression.
