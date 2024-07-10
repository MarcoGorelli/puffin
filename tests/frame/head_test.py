from __future__ import annotations

from typing import Any

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts


def test_head(constructor_with_lazy: Any) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df_raw = constructor_with_lazy(data)
    df = nw.from_native(df_raw).lazy()
    result = nw.to_native(df.head(2))
    expected = {"a": [1, 3], "b": [4, 4], "z": [7.0, 8.0]}
    compare_dicts(result, expected)
    result = nw.to_native(df.collect().head(2))
    expected = {"a": [1, 3], "b": [4, 4], "z": [7.0, 8.0]}
    compare_dicts(result, expected)
    result = nw.to_native(df.collect().select(nw.col("a").head(2)))
    expected = {"a": [1, 3]}
    compare_dicts(result, expected)
