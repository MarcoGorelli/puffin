from __future__ import annotations

import pytest

import narwhals.stable.v1 as nw
from tests.utils import Constructor
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data

data = {
    "i": [0, 1, 2, 3, 4],
    "a": [0, 1, 2, 3, 4],
    "b": [1, 2, 3, 5, 3],
    "c": [5, 4, 3, 2, 1],
}


def test_filter(constructor: Constructor, request: pytest.FixtureRequest) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor(data))
    result = df.select(nw.col("a").filter(nw.col("i") < 2, nw.col("c") == 5))
    expected = {"a": [0]}
    assert_equal_data(result, expected)


def test_filter_series(constructor_eager: ConstructorEager) -> None:
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.select(df["a"].filter((df["i"] < 2) & (df["c"] == 5)))
    expected = {"a": [0]}
    assert_equal_data(result, expected)
    result_s = df["a"].filter([True, False, False, False, False])
    expected = {"a": [0]}
    assert_equal_data({"a": result_s}, expected)


def test_filter_added_constraints(constructor: Constructor) -> None:
    df = nw.from_native(constructor(data))
    result = df.filter(nw.col("i") < 4, b=3)
    expected = {"i": [2], "a": [2], "b": [3], "c": [3]}
    assert_equal_data(result, expected)


def test_filter_only_constraints(constructor: Constructor) -> None:
    df = nw.from_native(constructor(data))
    result = df.filter(i=2, b=3)
    expected = {"i": [2], "a": [2], "b": [3], "c": [3]}
    assert_equal_data(result, expected)
