from __future__ import annotations

import argparse
from typing import Optional

from problemgen.app import build_domain_catalog, default_output_path, generate_problem_bundle
from problemgen.core.difficulty import DIFFICULTY_LEVELS
from problemgen.core.story_worlds import list_story_worlds
from problemgen.web.server import run_server


def parse_args() -> argparse.Namespace:
    catalog = build_domain_catalog()

    parser = argparse.ArgumentParser(
        description="Модульный генератор математических задач с локальным веб-интерфейсом."
    )
    parser.add_argument("--serve", action="store_true", help="Запустить локальный веб-сервер.")
    parser.add_argument("--host", default="127.0.0.1", help="Хост для веб-сервера.")
    parser.add_argument("--port", type=int, default=8000, help="Начальный порт для веб-сервера.")
    parser.add_argument("--domain", default="segments", choices=sorted(catalog), help="Блок задач.")
    parser.add_argument("--count", type=int, default=5, help="Количество задач.")
    parser.add_argument("--template-name", default="any", help="Имя шаблона внутри выбранного блока или any.")
    parser.add_argument(
        "--difficulty-level",
        default="medium",
        choices=sorted(DIFFICULTY_LEVELS),
        help="Уровень сложности: влияет на диапазоны чисел и вычислительную нагрузку.",
    )
    parser.add_argument("--story-theme", default="any", help="Код сюжетной темы.")
    parser.add_argument("--story-world", default="any", help="Ключ сюжетного мира.")
    parser.add_argument(
        "--list-story-worlds",
        action="store_true",
        help="Показать доступные сюжетные миры и завершить работу.",
    )
    parser.add_argument(
        "--seed-mode",
        default="today",
        choices=["today", "random", "fixed"],
        help="Режим генерации случайных чисел.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Число для fixed seed.")
    parser.add_argument(
        "--mode",
        default="all",
        choices=["all", "line", "plane"],
        help="Дополнительный фильтр для сегментных задач.",
    )
    parser.add_argument("--output", default=None, help="Куда сохранять JSON.")
    return parser.parse_args()


def print_bundle(bundle: dict) -> None:
    print(f"Сгенерировано {bundle['count_text']}.")
    print(f"Блок: {bundle['domain_label']}")
    print(f"Сложность: {bundle['difficulty_label']}")
    print(f"Тема: {bundle['requested_story_theme_label']}")
    print(f"Сюжетный мир: {bundle.get('requested_story_world_title', 'Любой мир')}")
    print("")

    for index, problem in enumerate(bundle["problems"], start=1):
        print(f"Задача {index} [{problem['code']}]")
        print(f"Шаблон: {problem['template_name']}")
        print(f"Условие: {problem['problem_text']}")
        print(f"Ответ: {problem['answer_text']}")
        issues = problem.get("metadata", {}).get("language_issues", [])
        if issues:
            print(f"Проверка русского: найдено замечаний {len(issues)}")
        print("-" * 72)

    print(f"JSON сохранен в файл: {bundle['output_path']}")


def print_story_worlds() -> None:
    print("Доступные сюжетные миры:")
    for world in list_story_worlds():
        print(f"- {world.key}: {world.title} [{world.location}]")


def run_cli(args: argparse.Namespace) -> None:
    if args.list_story_worlds:
        print_story_worlds()
        return
    output_path: Optional[str] = args.output or default_output_path(args.domain)
    bundle = generate_problem_bundle(
        domain_code=args.domain,
        count=args.count,
        template_name=args.template_name,
        difficulty_level=args.difficulty_level,
        story_theme=args.story_theme,
        story_world=args.story_world,
        seed_mode=args.seed_mode,
        seed=args.seed,
        output_path=output_path,
        options={"mode": args.mode},
    )
    print_bundle(bundle)


def main() -> None:
    args = parse_args()
    if args.list_story_worlds:
        run_cli(args)
        return
    if args.serve:
        run_server(args.host, args.port)
        return
    run_cli(args)


if __name__ == "__main__":
    main()
