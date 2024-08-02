from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {"a": list("xyz"), "b": [1, 2, 1]}
expected = {"a1": [2], "a2": [1]}


def test_len(constructor: Any, request: Any) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    df_raw = constructor(data)
    df = nw.from_native(df_raw).select(
        nw.col("a").filter(nw.col("b") == 1).len().alias("a1"),
        nw.col("a").filter(nw.col("b") == 2).len().alias("a2"),
    )

    compare_dicts(df, expected)
