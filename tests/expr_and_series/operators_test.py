from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts


@pytest.mark.parametrize(
    ("operator", "expected"),
    [
        ("__eq__", [False, True, False]),
        ("__ne__", [True, False, True]),
        ("__le__", [True, True, False]),
        ("__lt__", [True, False, False]),
        ("__ge__", [False, True, True]),
        ("__gt__", [False, False, True]),
    ],
)
def test_comparand_operators_scalar(
    constructor: Any, operator: str, expected: list[bool]
) -> None:
    data = {"a": [0, 1, 2]}
    df = nw.from_native(constructor(data))
    result = df.select(getattr(nw.col("a"), operator)(1))
    compare_dicts(result, {"a": expected})


@pytest.mark.parametrize(
    ("operator", "expected"),
    [
        ("__eq__", [True, False, False]),
        ("__ne__", [False, True, True]),
        ("__le__", [True, False, True]),
        ("__lt__", [False, False, True]),
        ("__ge__", [True, True, False]),
        ("__gt__", [False, True, False]),
    ],
)
def test_comparand_operators_expr(
    constructor: Any, operator: str, expected: list[bool]
) -> None:
    data = {"a": [0, 1, 1], "b": [0, 0, 2]}
    df = nw.from_native(constructor(data))
    result = df.select(getattr(nw.col("a"), operator)(nw.col("b")))
    compare_dicts(result, {"a": expected})


@pytest.mark.parametrize(
    ("operator", "expected"),
    [
        ("__and__", [True, False, False, False]),
        ("__or__", [True, True, True, False]),
    ],
)
def test_logic_operators(constructor: Any, operator: str, expected: list[bool]) -> None:
    data = {"a": [True, True, False, False], "b": [True, False, True, False]}
    df = nw.from_native(constructor(data))

    result = df.select(getattr(nw.col("a"), operator)(nw.col("b")))
    compare_dicts(result, {"a": expected})
