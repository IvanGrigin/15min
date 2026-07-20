# Автоматический Math Problem → JSON Template Creator

Маршрут `/admin/template-creator` принимает текст одной задачи и необязательный target module.
Нажатие «Создать шаблон» вызывает настроенный провайдер и показывает modal с полным JSON,
validation, warnings и тремя экземплярами. JSON создаётся автоматически, но независимо
проверяется до активации.

## Настройка провайдера

Провайдер — OpenAI-compatible HTTP endpoint. Задайте только в окружении процесса сайта:

```powershell
$env:TEMPLATE_CREATOR_PROVIDER_URL = "https://.../v1/chat/completions"
$env:TEMPLATE_CREATOR_API_KEY = "..."
$env:TEMPLATE_CREATOR_MODEL = "..."
python scripts/run_site.py
```

Без всех трёх переменных генератор не делает фиктивный fallback и сообщает
«Автоматический генератор шаблонов не настроен». Ключ, endpoint, internal prompt
и stack trace в браузер не передаются.

## JSON и проверка

Провайдер обязан вернуть только JSON, совместимый с
`data/template_creator/template_candidate.schema.json`. Нормализованная запись
содержит family, module, template text, независимые parameters, derived values,
constraints, grammar, confidence и warnings.

Поддерживаются `integer`, `decimal`, `fraction`, `boolean`, `word`, `word_list`,
`integer_list`, `ordered_list`, `multi_part` и `cryptarithm_solutions`. Runtime
сверяет фактический ответ с заявленным типом до активации.

Проверяются ID, module, answer type, зарегистрированная стратегия, границы
параметров, известные AST-переменные, плейсхолдеры, три fixed seed и тип ответа.
Для имён нужны явные род и требуемые формы без эвристического склонения.
`arithmetic_sequence_sum` дополнительно сверяется явным суммированием членов;
family без отдельного solver получает `activation_blocked`.

Сервис передаёт провайдеру только структурированный список ошибок и делает
максимум три repair-попытки. Последний JSON и ошибки остаются в draft.

## Публикация и ограничения

`Добавить в список` неактивна до успешной validation и при не реализованной
strategy. При успехе активируется структурированный overlay Template Studio;
production JSON модулей не переписывается. Draft можно создать заново
(предыдущая revision сохраняется) или подтверждённо удалить; active запись
этим интерфейсом не удаляется.
