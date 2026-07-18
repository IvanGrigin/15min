# Модуль 14: числовые процессы и повторяющиеся операции

ID `number_processes_and_repeated_operations`. В двух read-only источниках 8
уникальных задач после удаления 2 дублей. Все 8 активны: ограниченный Collatz до
порога, объединение трёх государств в одно, наложение нумерованных кругов и
следующий треугольный суммарный результат.

Каталог: `data/templates/problem_sets/number_processes_and_repeated_operations/`.
`problemgen/generation/process_templates.py` строит ограниченные процессы и
перепроверяет результаты независимой симуляцией/формулой. Для двух именованных
семейств персонаж выбирается из одной approved-вселенной; имя остаётся в
именительном падеже, без небезопасного склонения. Fixed seed воспроизводим.

Проверка: `py -3 scripts/validate_process_templates.py` и
`py -3 -m unittest tests.test_process_templates tests.test_worksheet_site`.
