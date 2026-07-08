# STORY_WORLDS

Этот файл описывает единый слой сюжетных миров, персонажей и локаций.

## Где хранится каталог

Единый источник данных:

- `problemgen/core/story_worlds.py`

Именно оттуда генераторы должны получать:

- название мира;
- локацию;
- персонажей;
- готовый `StoryContext` для шаблонов задач.

## Главные структуры

- `StoryWorld` — описание одного сюжетного мира;
- `StoryContext` — конкретный выбранный контекст для генерации одной задачи.

## Как использовать в коде

Основные функции:

- `get_story_world(key)`
- `list_story_worlds()`
- `sample_story_world(...)`
- `sample_story_context(...)`

Пример:

```python
from problemgen.core.story_worlds import sample_story_context

context = sample_story_context(world_key="smeshariki")
print(context.world_title)
print(context.location)
print(context.lead_character)
```

## Как использовать в CLI

Показать все доступные миры:

```bash
python3 scripts/run_problemgen.py --list-story-worlds
```

Выбрать конкретный мир:

```bash
python3 scripts/run_problemgen.py --domain counting --count 5 --story-world smeshariki
```

Использовать мир в олимпиадном домене:

```bash
python3 scripts/run_problemgen.py --domain olympiad_logic --template-name shared_payment_debt --count 3 --story-world fixiki
```

## Как добавить новый мир

1. Открыть `problemgen/core/story_worlds.py`
2. Добавить новый элемент в `STORY_WORLDS`
3. Указать:
   - `key`
   - `title`
   - `location`
   - минимум 4 персонажа в `characters`
4. При необходимости обновить документацию и тесты

## Правило для будущих генераторов

Нельзя дублировать список персонажей и локаций внутри отдельных генераторов.

Новые генераторы должны:

1. принимать `StoryContext`;
2. использовать `context.location` и `context.characters`;
3. записывать информацию о мире в поле `story` или `metadata`.

Хороший пример:

- `problemgen/domains/olympiad_logic/templates.py`
