"""Автоматическая проверка единого стиля — правила из docs/CODE_STYLE.md.

Правило, которое не проверяется машиной, через месяц перестаёт соблюдаться.
Здесь проверяется то, что можно проверить однозначно: регистр имён, наличие
докстрингов и то, что они написаны по-русски.
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CYRILLIC = re.compile("[а-яА-ЯёЁ]")
SNAKE_CASE_DIR = re.compile(r"^[a-z0-9_.-]+$")
SNAKE_CASE_MODULE = re.compile(r"^[a-z_][a-z0-9_]*\.py$")

# Каталоги, которые ведёт не проект: служебные и сторонние.
SKIPPED_DIRS = {".git", ".claude", "__pycache__", ".venv", "node_modules"}
# Пакеты, где живёт код проекта. tests/ проверяется отдельно и мягче:
# имя тест-метода само по себе описывает проверку.
CODE_ROOTS = ("problemgen", "scripts")


def project_python_files(*roots: str) -> list[Path]:
    """Собрать Python-файлы проекта, пропуская служебные каталоги."""
    files: list[Path] = []
    for root in roots:
        for path in sorted((PROJECT_ROOT / root).rglob("*.py")):
            if not SKIPPED_DIRS.intersection(path.parts):
                files.append(path)
    return files


def project_directories() -> list[Path]:
    """Все каталоги репозитория, кроме служебных."""
    return [
        path for path in sorted(PROJECT_ROOT.rglob("*"))
        if path.is_dir() and not SKIPPED_DIRS.intersection(path.parts)
    ]


class NamingTests(unittest.TestCase):
    def test_directories_are_lowercase(self) -> None:
        """Каталоги пишутся строчными: Docs и docs на Linux — разные пути."""
        for path in project_directories():
            name = path.name
            self.assertTrue(
                SNAKE_CASE_DIR.fullmatch(name),
                f"{path.relative_to(PROJECT_ROOT)}: имя каталога должно быть строчным snake_case",
            )

    def test_documentation_directory_has_one_spelling(self) -> None:
        """В репозитории ровно один каталог документации, и он называется docs."""
        variants = [
            path.name for path in PROJECT_ROOT.iterdir()
            if path.is_dir() and path.name.lower() == "docs"
        ]
        self.assertEqual(variants, ["docs"], f"найдено: {variants}")

    def test_python_modules_are_snake_case(self) -> None:
        for path in project_python_files(*CODE_ROOTS, "tests"):
            self.assertTrue(
                SNAKE_CASE_MODULE.fullmatch(path.name),
                f"{path.relative_to(PROJECT_ROOT)}: имя модуля должно быть строчным snake_case",
            )
        self.assertTrue(SNAKE_CASE_MODULE.fullmatch("run.py"))


class DocstringTests(unittest.TestCase):
    def public_definitions(self, tree: ast.Module):
        """Публичные функции, классы и методы верхнего уровня."""
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    yield node
            if isinstance(node, ast.ClassDef):
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not member.name.startswith("_"):
                            yield member

    def test_modules_have_russian_docstrings(self) -> None:
        for path in project_python_files(*CODE_ROOTS) + [PROJECT_ROOT / "run.py"]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            doc = ast.get_docstring(tree)
            relative = path.relative_to(PROJECT_ROOT)
            if path.name == "__init__.py" and not (tree.body and doc):
                continue
            self.assertTrue(doc, f"{relative}: нет докстринга модуля")
            self.assertRegex(doc, CYRILLIC, f"{relative}: докстринг модуля не на русском")

    def test_public_definitions_have_russian_docstrings(self) -> None:
        for path in project_python_files(*CODE_ROOTS) + [PROJECT_ROOT / "run.py"]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            relative = path.relative_to(PROJECT_ROOT)
            for node in self.public_definitions(tree):
                doc = ast.get_docstring(node)
                self.assertTrue(doc, f"{relative}:{node.lineno} {node.name}: нет докстринга")
                self.assertRegex(
                    doc, CYRILLIC,
                    f"{relative}:{node.lineno} {node.name}: докстринг не на русском",
                )

    def test_no_english_only_docstrings_anywhere(self) -> None:
        """Даже в тестах: если докстринг написан, он на русском."""
        for path in project_python_files(*CODE_ROOTS, "tests") + [PROJECT_ROOT / "run.py"]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            relative = path.relative_to(PROJECT_ROOT)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    continue
                doc = ast.get_docstring(node)
                if doc and not CYRILLIC.search(doc):
                    name = getattr(node, "name", "модуль")
                    self.fail(f"{relative}: докстринг {name} не на русском: {doc.splitlines()[0][:60]}")


class FormattingTests(unittest.TestCase):
    def test_no_semicolon_one_liners(self) -> None:
        """Однострочники через «;» — стиль архивного кода, повторять не нужно.

        Ищем именно оператор-разделитель через токенизатор: точка с запятой
        внутри строки или комментария — обычный текст и нарушением не является.
        """
        import io
        import tokenize

        for path in project_python_files(*CODE_ROOTS, "tests") + [PROJECT_ROOT / "run.py"]:
            source = path.read_text(encoding="utf-8")
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                if token.type == tokenize.OP and token.string == ";":
                    self.fail(
                        f"{path.relative_to(PROJECT_ROOT)}:{token.start[0]}: "
                        f"{token.line.strip()[:70]}"
                    )

    def test_lines_are_not_too_long(self) -> None:
        limit = 110
        offenders = []
        for path in project_python_files(*CODE_ROOTS) + [PROJECT_ROOT / "run.py"]:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if len(line) > limit:
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{number} ({len(line)})")
        self.assertEqual(offenders, [], f"строк длиннее {limit} символов: {offenders[:10]}")


if __name__ == "__main__":
    unittest.main()
