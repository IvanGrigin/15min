# `problemgen/template_creator`

Автоматический provider-backed слой «математическая задача → JSON-шаблон».

- `provider.py` — Protocol и OpenAI-compatible адаптер конфигурации окружения;
- `service.py` — bounded repair loop, strict validation, preview и activation;
- `storage.py` — отдельное atomic draft-хранилище.

Пакет не зависит от frontend и не исполняет provider output как Python или JS.
Безопасный runtime и active overlay переиспользуются из `template_studio`.
