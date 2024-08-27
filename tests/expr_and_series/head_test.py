from __future__ import annotations

from typing import Any

import pytest

import narwhals as nw
from tests.utils import compare_dicts


@pytest.mark.parametrize("n", [2, -1])
def test_head(constructor: Any, n: int, request: Any) -> None:
    if "polars" in str(constructor) and n < 0:
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor({"a": [1, 2, 3]}))
    result = df.select(nw.col("a").head(n))
    expected = {"a": [1, 2]}
    compare_dicts(result, expected)


@pytest.mark.parametrize("n", [2, -1])
def test_head_series(constructor_eager: Any, n: int) -> None:
    df = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)
    result = df.select(df["a"].head(n))
    expected = {"a": [1, 2]}
    compare_dicts(result, expected)
