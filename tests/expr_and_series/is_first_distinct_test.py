from typing import Any

import numpy as np

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {
    "a": [1, 1, 2, 3, 2],
    "b": [1, 2, 3, 2, 1],
}


def test_is_first_distinct_expr(constructor: Any) -> None:
    df = nw.from_native(constructor(data), eager_only=True)
    result = df.select(nw.all().is_first_distinct())
    expected = {
        "a": [True, False, True, True, False],
        "b": [True, True, True, False, False],
    }
    compare_dicts(result, expected)


def test_is_first_distinct_series(constructor_series: Any) -> None:
    series = nw.from_native(constructor_series(data["a"]), series_only=True)
    result = series.is_first_distinct()
    expected = np.array([True, False, True, True, False])
    assert (result.to_numpy() == expected).all()
