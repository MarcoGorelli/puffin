from __future__ import annotations

from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version
from tests.utils import compare_dicts

data = {
    "a": [
        None,
        timedelta(minutes=1, seconds=1, milliseconds=1, microseconds=1),
    ],
    "b": [
        timedelta(milliseconds=2),
        timedelta(milliseconds=1, microseconds=300),
    ],
    "c": np.array([None, 20], dtype="timedelta64[ns]"),
    "d": [
        timedelta(milliseconds=2),
        timedelta(seconds=1),
    ],
}


@pytest.mark.parametrize(
    ("attribute", "expected_a", "expected_b"),
    [
        ("total_minutes", [0, 1], [0, 0]),
        ("total_seconds", [0, 61], [0, 0]),
        ("total_milliseconds", [0, 61001], [2, 1]),
    ],
)
def test_duration_attributes(
    request: Any,
    constructor_eager: Any,
    attribute: str,
    expected_a: list[int],
    expected_b: list[int],
) -> None:
    if parse_version(pd.__version__) < (2, 2) and "pandas_pyarrow" in str(
        constructor_eager
    ):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_eager(data), eager_only=True)
    result_a = df.select(getattr(nw.col("a").dt, attribute)().fill_null(0))
    compare_dicts(result_a, {"a": expected_a})

    result_a = df.select(getattr(df["a"].dt, attribute)().fill_null(0))
    compare_dicts(result_a, {"a": expected_a})

    result_b = df.select(getattr(nw.col("b").dt, attribute)().fill_null(0))
    compare_dicts(result_b, {"b": expected_b})

    result_b = df.select(getattr(df["b"].dt, attribute)().fill_null(0))
    compare_dicts(result_b, {"b": expected_b})


@pytest.mark.parametrize(
    ("attribute", "expected_b", "expected_c"),
    [
        ("total_microseconds", [2000, 1300], [0, 0]),
        ("total_nanoseconds", [2000000, 1300000], [0, 20]),
    ],
)
def test_duration_micro_nano(
    request: Any,
    constructor_eager: Any,
    attribute: str,
    expected_b: list[int],
    expected_c: list[int],
) -> None:
    if parse_version(pd.__version__) < (2, 2) and "pandas_pyarrow" in str(
        constructor_eager
    ):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_eager(data), eager_only=True)

    result_b = df.select(getattr(nw.col("b").dt, attribute)().fill_null(0))
    compare_dicts(result_b, {"b": expected_b})

    result_b = df.select(getattr(df["b"].dt, attribute)().fill_null(0))
    compare_dicts(result_b, {"b": expected_b})

    result_c = df.select(getattr(nw.col("c").dt, attribute)().fill_null(0))
    compare_dicts(result_c, {"c": expected_c})

    result_c = df.select(getattr(df["c"].dt, attribute)().fill_null(0))
    compare_dicts(result_c, {"c": expected_c})


@pytest.mark.parametrize("unit", ["s", "ms", "us", "ns"])
@pytest.mark.parametrize(
    ("attribute", "expected"),
    [
        ("total_minutes", 1),
        ("total_seconds", 70),
        ("total_milliseconds", 70e3),
        ("total_microseconds", 70e6),
        ("total_nanoseconds", 70e9),
    ],
)
def test_pyarrow_units(unit: str, attribute: str, expected: int) -> None:
    data = [None, timedelta(minutes=1, seconds=10)]
    arr = pc.cast(pa.array(data), pa.duration(unit))
    df = nw.from_native(pa.table({"a": arr}), eager_only=True)

    result_expr = df.select(getattr(nw.col("a").dt, attribute)().fill_null(0))
    compare_dicts(result_expr, {"a": [0, expected]})

    result_series = df.select(getattr(df["a"].dt, attribute)().fill_null(0))
    compare_dicts(result_series, {"a": [0, expected]})
