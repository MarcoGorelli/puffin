from typing import Any

import numpy as np
import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {
    "a": [1, 1, 2, 3, 2],
    "b": [1, 2, 3, 2, 1],
}


def test_is_first_distinct_expr(constructor_lazy: Any, request: Any) -> None:
    if "modin" in str(constructor_lazy):
        # TODO(unassigned): why is Modin failing here?
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor_lazy(data))
    result = df.select(nw.all().is_first_distinct())
    expected = {
        "a": [True, False, True, True, False],
        "b": [True, True, True, False, False],
    }
    compare_dicts(result, expected)


def test_is_first_distinct_series(constructor: Any) -> None:
    series = nw.from_native(constructor(data), eager_only=True)["a"]
    result = series.is_first_distinct()
    expected = np.array([True, False, True, True, False])
    assert (result.to_numpy() == expected).all()
