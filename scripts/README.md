# scripts

Инструменты подготовки данных и публикации шаблонов. Генераторов задач здесь
нет и не должно быть: задача описывается JSON-записью, см. `../AGENTS.md`.

| Скрипт | Что делает |
|---|---|
| `seed_worksheet_templates.py` | публикует шаблоны из `data/template_studio/library/` через draft → validate → activate |
| `review_queue.py` | компактный дайджест шаблонов на проверку |
| `declension_rules.py` | правила склонения — **только** для подготовки данных, не рантайм |
| `data_agent_loop.py` | заготовки словоформ по правилам для очереди слов |
| `data_review.py` | разбор заготовок и приём их в словарь |

## Типовые команды

```bash
python3 scripts/seed_worksheet_templates.py --preview --only <template_id>
```

```bash
python3 scripts/seed_worksheet_templates.py --only <template_id>
```

```bash
python3 scripts/data_agent_loop.py --queue data/language/queue/nouns.json
```

```bash
python3 scripts/data_review.py
```
