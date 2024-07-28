from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}


@pytest.mark.parametrize("expr", [nw.col("a", "b", "z").min(), nw.min("a", "b", "z")])
def test_expr_min_expr(constructor: Any, expr: nw.Expr) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(expr)
    expected = {"a": [1], "b": [4], "z": [7.0]}
    compare_dicts(result, expected)


@pytest.mark.parametrize(("col", "expected"), [("a", 1), ("b", 4), ("z", 7.0)])
def test_expr_min_series(constructor_eager: Any, col: str, expected: float) -> None:
    series = nw.from_native(constructor_eager(data), eager_only=True)[col]
    result = series.min()
    compare_dicts({col: [result]}, {col: [expected]})
