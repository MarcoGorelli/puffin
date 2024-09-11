from typing import Any

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts


def test_slice(constructor_eager: Any) -> None:
    data = {"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9], "d": [1, 4, 2]}
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = {"a": df["a"][[0, 1]]}
    expected = {"a": [1, 2]}
    compare_dicts(result, expected)
    result = {"a": df["a"][1:]}
    expected = {"a": [2, 3]}
    compare_dicts(result, expected)
