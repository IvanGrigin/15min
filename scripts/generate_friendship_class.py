import json
import math
import random
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.core.story_worlds import sample_story_context

PIONEER_WORDS = ["пионер", "отличник", "кружковец", "спортсмен"]


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def build_problem(index: int) -> dict[str, object]:
    story_context = sample_story_context(random)
    name = story_context.lead_character
    extra_word = random.choice(PIONEER_WORDS)

    # Выбираем соотношение так, чтобы количество мальчиков и девочек было целым.
    boys_per_girl = random.randint(2, 6)
    girls_per_boy = random.randint(2, 6)

    gcd_value = math.gcd(boys_per_girl, girls_per_boy)
    boys_ratio = boys_per_girl // gcd_value
    girls_ratio = girls_per_boy // gcd_value

    multiplier = random.randint(3, 12)
    boys = boys_ratio * multiplier
    girls = girls_ratio * multiplier
    total_students = boys + girls
    desks = total_students // 2

    # Делаем общее число учеников четным, чтобы оно совпадало с числом мест за партами.
    if total_students % 2 != 0:
        multiplier *= 2
        boys = boys_ratio * multiplier
        girls = girls_ratio * multiplier
        total_students = boys + girls
        desks = total_students // 2

    extra_count = random.randint(max(1, total_students // 3), total_students - 1)

    condition = (
        f"{index}. В мире «{story_context.world_title}» {name} учился в классе, где каждый мальчик дружил с "
        f"{girls_per_boy} девочками, а каждая девочка — с {boys_per_girl} мальчиками. "
        f"При этом в классе было {extra_count} "
        f"{plural(extra_count, extra_word, extra_word + 'а', extra_word + 'ов')} "
        f"и стояло {desks} {plural(desks, 'парта', 'парты', 'парт')}. "
        f"Сколько учеников было в этом классе?"
    )
    return {
        "id": index,
        "condition": condition,
        "answer": total_students,
        "story": story_context.to_metadata(),
    }


def main() -> None:
    random.seed()
    problems = [build_problem(i) for i in range(1, 1001)]

    output_path = PROJECT_ROOT / "outputs" / "friendship_class" / "1000_zadach.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(problems, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Готово: создан файл {output_path.resolve()}")


if __name__ == "__main__":
    main()
