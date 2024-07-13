from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw


@pytest.mark.parametrize(("threshold", "expected"), [(0, False), (10, True)])
def test_is_empty(constructor: Any, threshold: Any, expected: Any) -> None:
    if "pyarrow_table" in str(constructor):
        pytest.xfail()
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df_raw = constructor(data)
    df = nw.from_native(df_raw, eager_only=True)
    result = df.filter(nw.col("a") > threshold).is_empty()
    assert result == expected
