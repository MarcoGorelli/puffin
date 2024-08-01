from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts


def test_rename(constructor: Any, request: Any) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df = nw.from_native(constructor(data))
    result = df.rename({"a": "x", "b": "y"})
    expected = {"x": [1, 3, 2], "y": [4, 4, 6], "z": [7.0, 8, 9]}
    compare_dicts(result, expected)
