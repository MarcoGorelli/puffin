from __future__ import annotations

from typing import Any

import pytest

import narwhals as nw
from tests.utils import compare_dicts


def test_scatter(constructor_eager: Any, request: pytest.FixtureRequest) -> None:
    if "modin" in str(constructor_eager):
        # https://github.com/modin-project/modin/issues/7392
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(
        constructor_eager({"a": [1, 2, 3], "b": [142, 124, 132]}), eager_only=True
    )
    result = df.with_columns(
        df["a"].scatter([0, 1], [999, 888]),
        df["b"].scatter([0, 2, 1], df["b"]),
    )
    expected = {
        "a": [999, 888, 3],
        "b": [142, 132, 124],
    }
    compare_dicts(result, expected)
