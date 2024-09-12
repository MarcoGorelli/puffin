from typing import Any

import polars as pl
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version
from tests.utils import compare_dicts

data = {
    "a": [1, 1, 2, 2, 3],
    "b": [1, 2, 3, 3, 4],
}


def test_mode_single_expr(constructor: Any, request: Any) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data))
    result = df.select(nw.col("a").mode()).sort("a")
    expected = {"a": [1, 2]}
    compare_dicts(result, expected)


def test_mode_multi_expr(constructor: Any, request: Any) -> None:
    if "dask" in str(constructor) or (
        "polars" in str(constructor) and parse_version(pl.__version__) >= (1, 7, 0)
    ):
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor(data))
    result = df.select(nw.col("a", "b").mode()).sort("a", "b")
    expected = {"a": [1, 2], "b": [3, 3]}
    compare_dicts(result, expected)


def test_mode_series(constructor_eager: Any) -> None:
    series = nw.from_native(constructor_eager(data), eager_only=True)["a"]
    result = series.mode().sort()
    expected = {"a": [1, 2]}
    compare_dicts({"a": result}, expected)
