from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {"a": [1, 3, 2], "b": [4, 4, 7], "z": [7.0, 8, 9]}


@pytest.mark.parametrize("expr", [nw.col("a", "b", "z").mean(), nw.mean("a", "b", "z")])
def test_expr_mean_expr(constructor: Any, expr: nw.Expr) -> None:
    df = nw.from_native(constructor(data), eager_only=True)
    result = df.select(expr)
    expected = {"a": [2.0], "b": [5.0], "z": [8.0]}
    compare_dicts(result, expected)


@pytest.mark.parametrize(("col", "expected"), [("a", 2.0), ("b", 5.0), ("z", 8.0)])
def test_expr_mean_series(constructor_series: Any, col: str, expected: float) -> None:
    series = nw.from_native(constructor_series(data[col]), series_only=True)
    result = series.mean()
    compare_dicts({col: [result]}, {col: [expected]})
