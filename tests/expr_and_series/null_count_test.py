from typing import Any

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {
    "a": [1.0, None, None, 3.0],
    "b": [1.0, None, 4, 5.0],
}


def test_null_count_expr(constructor: Any) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(nw.all().null_count())
    expected = {
        "a": [2],
        "b": [1],
    }
    compare_dicts(result, expected)


def test_null_count_series(constructor_eager: Any) -> None:
    data = [1, 2, None]
    series = nw.from_native(constructor_eager({"a": data}), eager_only=True)["a"]
    result = series.null_count()
    assert result == 1
