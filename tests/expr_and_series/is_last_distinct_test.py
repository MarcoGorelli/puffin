from typing import Any

import numpy as np

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {
    "a": [1, 1, 2, 3, 2],
    "b": [1, 2, 3, 2, 1],
}


def test_is_last_distinct_expr(constructor: Any) -> None:
    df = nw.from_native(constructor(data), eager_only=True)
    result = df.select(nw.all().is_last_distinct())
    expected = {
        "a": [False, True, False, True, True],
        "b": [False, False, True, True, True],
    }
    compare_dicts(result, expected)


def test_is_last_distinct_series(constructor_series: Any) -> None:
    series = nw.from_native(constructor_series(data["a"]), series_only=True)
    result = series.is_last_distinct()
    expected = np.array([False, True, False, True, True])
    assert (result.to_numpy() == expected).all()
