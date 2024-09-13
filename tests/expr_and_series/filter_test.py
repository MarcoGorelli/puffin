from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import Constructor
from tests.utils import compare_dicts

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
    compare_dicts(result, expected)


def test_filter_series(constructor_eager: Any) -> None:
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.select(df["a"].filter((df["i"] < 2) & (df["c"] == 5)))
    expected = {"a": [0]}
    compare_dicts(result, expected)
    result_s = df["a"].filter([True, False, False, False, False])
    expected = {"a": [0]}
    compare_dicts({"a": result_s}, expected)
