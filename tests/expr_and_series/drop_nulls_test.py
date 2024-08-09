from __future__ import annotations

from typing import Any

import pytest

import narwhals as nw
from tests.utils import compare_dicts


def test_drop_nulls(constructor: Any, request: Any) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    data = {
        "A": [1, 2, None, 4],
        "B": [5, 6, 7, 8],
        "C": [None, None, None, None],
        "D": [9, 10, 11, 12],
    }

    df = nw.from_native(constructor(data))

    result_a = df.select(nw.col("A").drop_nulls())
    result_b = df.select(nw.col("B").drop_nulls())
    result_c = df.select(nw.col("C").drop_nulls())
    result_d = df.select(nw.col("D").drop_nulls())
    expected_a = {"A": [1.0, 2.0, 4.0]}
    expected_b = {"B": [5, 6, 7, 8]}
    expected_c = {"C": []}  # type: ignore[var-annotated]
    expected_d = {"D": [9, 10, 11, 12]}

    compare_dicts(result_a, expected_a)
    compare_dicts(result_b, expected_b)
    compare_dicts(result_c, expected_c)
    compare_dicts(result_d, expected_d)


def test_drop_nulls_series(constructor_eager: Any) -> None:
    data = {
        "A": [1, 2, None, 4],
        "B": [5, 6, 7, 8],
        "C": [None, None, None, None],
        "D": [9, 10, 11, 12],
    }

    df = nw.from_native(constructor_eager(data), eager_only=True)

    result_a = df.select(df["A"].drop_nulls())
    result_b = df.select(df["B"].drop_nulls())
    result_c = df.select(df["C"].drop_nulls())
    result_d = df.select(df["D"].drop_nulls())
    expected_a = {"A": [1.0, 2.0, 4.0]}
    expected_b = {"B": [5, 6, 7, 8]}
    expected_c = {"C": []}  # type: ignore[var-annotated]
    expected_d = {"D": [9, 10, 11, 12]}

    compare_dicts(result_a, expected_a)
    compare_dicts(result_b, expected_b)
    compare_dicts(result_c, expected_c)
    compare_dicts(result_d, expected_d)
