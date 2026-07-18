# Production каталог 15-минуток

- Каталог: `data/templates/problem_templates.json` (правки — скриптом, не руками).
- Движок: `problemgen/generation/template_generator.py` — стратегии
  `@_number_strategy(...)`, вычислитель `answer_formula`, белый список `_FUNCTIONS`.
- Ворклист покрытия корпуса: `data/source_index/per_task_template_worklist.json`
  (после закрытия листа проставить `status: "done"`).
- Страж хрупкости: `tests/...::test_no_template_is_fragile_across_seeds` — обязан
  быть зелёным после любых правок стратегий/границ.
- Гарантированное целое деление и обратная проверка — образец
  `arithmetic_a02_nested_expression`; календарь/часы — авторские I01–I08.
