# Архивный recovery

Ответы для очищенных архивных записей — только overlay
`data/templates/all_tasks_answer_recovery.json` поверх неизменяемого
`all_tasks_templates.json`; применение — `problemgen/worksheet/all_tasks_site.py`
(`RECOVERY_GENERATION_STRATEGIES` для связанных параметров).

Жёсткие правила: формула обязана давать ровно `source_answer` на
`original_values`; тест в `tests/test_worksheet_site.py` — минимум 25 seed;
непроверенные записи НЕ получают выдуманный ответ; OCR-обрыв или неоднозначность
= стоп. Полный протокол — `Docs/TEMPLATE_AUTHORING_GUIDE.md`.
