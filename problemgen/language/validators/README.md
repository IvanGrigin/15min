# problemgen/language/validators

Здесь должны жить проверки языковой корректности.

## Задачи слоя

- проверять наличие всех форм и слотов;
- проверять отсутствие необработанных плейсхолдеров;
- проверять согласование и trace-данные;
- формировать понятный validation report.

## Примеры будущих функций

- `validate_rendered_problem()`
- `validate_language_trace()`
- `validate_slot_coverage()`
