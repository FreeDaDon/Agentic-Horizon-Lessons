"""The calculator tool evaluates arithmetic and nothing else, run offline."""

import asyncio
import math

import pytest

from calc_agent import calculate_expression, evaluate_math


@pytest.mark.parametrize("expression,expected", [
    ("2 + 3 * 4", 14),
    ("(2 + 3) * 4", 20),
    ("7 / 2", 3.5),
    ("7 // 2", 3),
    ("7 % 3", 1),
    ("2 ** 10", 1024),
    ("-3 + +5", 2),
    ("2 ** -1", 0.5),
    ("sqrt(16) + pi", 4 + math.pi),
    ("sin(0) + cos(0)", 1.0),
    ("log(e)", 1.0),
    ("factorial(10)", 3628800),
    ("abs(-4) + round(2.567, 1)", 6.6),
    ("max(1, 5, 3) - min(4, 2)", 3),
    ("sum([1, 2, 3])", 6),
    ("10 ** 100", 10 ** 100),
])
def test_ordinary_math_still_works(expression, expected):
    assert evaluate_math(expression) == pytest.approx(expected)


@pytest.mark.parametrize("expression", [
    "().__class__.__base__.__subclasses__()",
    "__import__('os')",
    "__import__('os').system('id')",
    "(1).__class__",
    "math.sqrt(4)",
    "sqrt.__self__",
    "'a' * 3",
    "[x for x in range(3)]",
    "(lambda: 1)()",
    "open('/etc/passwd')",
    "eval('1')",
    "round(2.5, ndigits=1)",
    "True + 1",
    "1 << 10",
    "x := 1",
])
def test_anything_but_arithmetic_is_rejected(expression):
    with pytest.raises((ValueError, SyntaxError)):
        evaluate_math(expression)


@pytest.mark.parametrize("expression", [
    "9 ** 9 ** 9",
    "10 ** 100000",
    "(10 ** 10000) ** 1000",
    "factorial(10 ** 8)",
    "comb(10 ** 9, 10 ** 5)",
])
def test_expressions_that_would_pin_the_cpu_are_rejected(expression):
    with pytest.raises(ValueError):
        evaluate_math(expression)


def call_tool(expression: str) -> dict:
    return asyncio.run(calculate_expression.handler({"expression": expression, "precision": 3}))


def test_the_tool_reports_a_result():
    assert call_tool("1 / 3") == {"content": [{"type": "text", "text": "Result: 0.333"}]}


def test_the_tool_reports_an_escape_attempt_as_an_error():
    result = call_tool("().__class__.__base__.__subclasses__()")
    assert result["is_error"] is True
    assert "Calculation error" in result["content"][0]["text"]
