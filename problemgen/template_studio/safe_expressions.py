"""Небольшой безопасный вычислитель формул Template Studio.

В отличие от ``eval`` он обходит только заранее разрешённые AST-узлы и не
принимает атрибуты, импорты, лямбды или произвольные вызовы.
"""

from __future__ import annotations

import ast
import math
import operator
from fractions import Fraction
from typing import Any


class SafeExpressionError(ValueError):
    """Выражение не принадлежит разрешённому математическому подмножеству."""


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
_COMPARE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}
_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "gcd": math.gcd,
    "lcm": math.lcm,
    "factorial": math.factorial,
}


def expression_names(expression: str) -> set[str]:
    """Возвращает имена переменных и функций после безопасного разбора."""
    tree = _parse(expression)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def validate_expression(expression: str, allowed_variables: set[str]) -> None:
    """Проверяет синтаксис и неизвестные имена без выполнения выражения."""
    tree = _parse(expression)
    _validate_tree(tree, allowed_variables)


def evaluate_expression(expression: str, variables: dict[str, Any]) -> Any:
    """Вычисляет арифметическое выражение только из разрешённых элементов."""
    tree = _parse(expression)
    _validate_tree(tree, set(variables))

    def visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, bool, str)):
            return node.value
        if isinstance(node, ast.Name):
            return variables[node.id]
        if isinstance(node, ast.List):
            return [visit(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(visit(item) for item in node.elts)
        if isinstance(node, ast.UnaryOp):
            return _UNARY_OPERATORS[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (not isinstance(right, int) or not 0 <= right <= 64):
                raise SafeExpressionError("Показатель степени должен быть целым числом от 0 до 64.")
            if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
                raise SafeExpressionError("Деление на ноль в выражении запрещено.")
            # Морфологические значения (существительное, персонаж, локация) — это
            # объекты с парадигмой, а не числа. Без явной проверки Python бросает
            # TypeError, который наверх уходит как падение, а не как понятный отказ.
            for operand in (left, right):
                if not isinstance(operand, (int, float, Fraction)) or isinstance(operand, bool):
                    raise SafeExpressionError(
                        "В арифметическом выражении можно использовать только числа. "
                        "Параметры типа noun, character и location — слова, а не величины: "
                        "заведите отдельный числовой параметр."
                    )
            return _BINARY_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.Compare):
            left = visit(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                right = visit(comparator)
                if not _COMPARE_OPERATORS[type(operation)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.BoolOp):
            values = [visit(value) for value in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.IfExp):
            return visit(node.body) if visit(node.test) else visit(node.orelse)
        if isinstance(node, ast.Call):
            function = _FUNCTIONS[node.func.id]
            arguments = [visit(argument) for argument in node.args]
            if node.func.id in {"gcd", "lcm", "factorial"}:
                if any(not isinstance(argument, int) or isinstance(argument, bool) for argument in arguments):
                    raise SafeExpressionError(f"{node.func.id} принимает только целые числа.")
            if node.func.id == "factorial" and (len(arguments) != 1 or arguments[0] < 0 or arguments[0] > 1000):
                raise SafeExpressionError("factorial принимает одно целое число от 0 до 1000.")
            return function(*arguments)
        raise SafeExpressionError("Недопустимый элемент выражения.")

    result = visit(tree)
    if isinstance(result, Fraction) and result.denominator == 1:
        return result.numerator
    if isinstance(result, float) and not math.isfinite(result):
        raise SafeExpressionError("Результат выражения должен быть конечным числом.")
    return result


def _parse(expression: str) -> ast.Expression:
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 1000:
        raise SafeExpressionError("Выражение должно быть непустой строкой не длиннее 1000 символов.")
    try:
        return ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise SafeExpressionError("Некорректный синтаксис математического выражения.") from error


def _validate_tree(tree: ast.AST, allowed_variables: set[str]) -> None:
    allowed_nodes = (
        ast.Expression, ast.Constant, ast.Name, ast.Load, ast.List, ast.Tuple,
        ast.UnaryOp, ast.UAdd, ast.USub, ast.Not, ast.BinOp, ast.Add, ast.Sub, ast.Mult,
        ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.Call,
        # Сравнения и логика нужны для constraints (пересэмплирование) и для
        # условных ответов вида "a if a > b else b".
        ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.BoolOp, ast.And, ast.Or, ast.IfExp,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise SafeExpressionError(f"Недопустимый элемент выражения: {type(node).__name__}.")
        if isinstance(node, ast.Name) and node.id not in allowed_variables | set(_FUNCTIONS):
            raise SafeExpressionError(f"Неизвестная переменная или функция: {node.id}.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS or node.keywords:
                raise SafeExpressionError("Разрешены только прямые вызовы функций из белого списка.")
