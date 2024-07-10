from __future__ import annotations

from typing import Any

import numpy as np

import narwhals.stable.v1 as nw


def test_convert_numpy(constructor: Any) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df_raw = constructor(data)
    result = nw.from_native(df_raw, eager_only=True).to_numpy()

    expected = np.array([[1, 3, 2], [4, 4, 6], [7.0, 8, 9]]).T
    np.testing.assert_array_equal(result, expected)
    assert result.dtype == "float64"

    result = nw.from_native(df_raw, eager_only=True).__array__()
    np.testing.assert_array_equal(result, expected)
    assert result.dtype == "float64"
