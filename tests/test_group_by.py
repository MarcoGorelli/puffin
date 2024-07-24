from __future__ import annotations

from contextlib import nullcontext
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version
from tests.utils import compare_dicts

data = {"a": [1, 1, 3], "b": [4, 4, 6], "c": [7.0, 8, 9]}

df_pandas = pd.DataFrame(data)
df_lazy = pl.LazyFrame(data)


def test_group_by_complex() -> None:
    expected = {"a": [1, 3], "b": [-3.5, -3.0]}

    df = nw.from_native(df_pandas)
    with pytest.warns(UserWarning, match="complex group-by"):
        result = nw.to_native(
            df.group_by("a").agg((nw.col("b") - nw.col("c").mean()).mean()).sort("a")
        )
    compare_dicts(result, expected)

    lf = nw.from_native(df_lazy).lazy()
    result = nw.to_native(
        lf.group_by("a").agg((nw.col("b") - nw.col("c").mean()).mean()).sort("a")
    )
    compare_dicts(result, expected)


def test_invalid_group_by() -> None:
    df = nw.from_native(df_pandas)
    with pytest.raises(RuntimeError, match="does your"):
        df.group_by("a").agg(nw.col("b"))
    with pytest.raises(
        ValueError, match=r"Anonymous expressions are not supported in group_by\.agg"
    ):
        df.group_by("a").agg(nw.all().mean())
    with pytest.raises(
        ValueError, match=r"Anonymous expressions are not supported in group_by\.agg"
    ):
        nw.from_native(pa.table({"a": [1, 2, 3]})).group_by("a").agg(nw.all().mean())
    with pytest.raises(ValueError, match=r"Non-trivial complex found"):
        nw.from_native(pa.table({"a": [1, 2, 3]})).group_by("a").agg(
            nw.col("b").mean().min()
        )


def test_group_by_iter(request: Any, constructor: Any) -> None:
    if "pyarrow_table" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data), eager_only=True)
    expected_keys = [(1,), (3,)]
    keys = []
    for key, sub_df in df.group_by("a"):
        if key == (1,):
            expected = {"a": [1, 1], "b": [4, 4], "c": [7.0, 8.0]}
            compare_dicts(sub_df, expected)
            assert isinstance(sub_df, nw.DataFrame)
        keys.append(key)
    assert sorted(keys) == sorted(expected_keys)
    expected_keys = [(1, 4), (3, 6)]  # type: ignore[list-item]
    keys = []
    for key, _df in df.group_by("a", "b"):
        keys.append(key)
    assert sorted(keys) == sorted(expected_keys)
    keys = []
    for key, _df in df.group_by(["a", "b"]):
        keys.append(key)
    assert sorted(keys) == sorted(expected_keys)


def test_group_by_len(request: Any, constructor: Any) -> None:
    if "pyarrow_table" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    result = (
        nw.from_native(constructor(data)).group_by("a").agg(nw.col("b").len()).sort("a")
    )
    expected = {"a": [1, 3], "b": [2, 1]}
    compare_dicts(result, expected)


def test_group_by_empty_result_pandas() -> None:
    df_any = pd.DataFrame({"a": [1, 2, 3], "b": [4, 3, 2]})
    df = nw.from_native(df_any, eager_only=True)
    with pytest.raises(ValueError, match="No results"):
        df.filter(nw.col("a") < 0).group_by("a").agg(
            nw.col("b").sum().round(2).alias("c")
        )


def test_group_by_simple_named(constructor: Any) -> None:
    data = {"a": [1, 1, 2], "b": [4, 5, 6], "c": [7, 2, 1]}
    df = nw.from_native(constructor(data), eager_only=True)
    result = (
        df.group_by("a")
        .agg(
            b_min=nw.col("b").min(),
            b_max=nw.col("b").max(),
        )
        .sort("a")
    )
    expected = {
        "a": [1, 2],
        "b_min": [4, 6],
        "b_max": [5, 6],
    }
    compare_dicts(result, expected)


def test_group_by_simple_unnamed(constructor: Any) -> None:
    data = {"a": [1, 1, 2], "b": [4, 5, 6], "c": [7, 2, 1]}
    df = nw.from_native(constructor(data), eager_only=True)
    result = (
        df.group_by("a")
        .agg(
            nw.col("b").min(),
            nw.col("c").max(),
        )
        .sort("a")
    )
    expected = {
        "a": [1, 2],
        "b": [4, 6],
        "c": [7, 1],
    }
    compare_dicts(result, expected)


def test_group_by_multiple_keys(constructor: Any) -> None:
    data = {"a": [1, 1, 2], "b": [4, 4, 6], "c": [7, 2, 1]}
    df = nw.from_native(constructor(data), eager_only=True)
    result = (
        df.group_by("a", "b")
        .agg(
            c_min=nw.col("c").min(),
            c_max=nw.col("c").max(),
        )
        .sort("a")
    )
    expected = {
        "a": [1, 2],
        "b": [4, 6],
        "c_min": [2, 1],
        "c_max": [7, 1],
    }
    compare_dicts(result, expected)


def test_key_with_nulls(constructor: Any) -> None:
    context = (
        pytest.raises(NotImplementedError, match="null values")
        if (
            "pandas_constructor" in str(constructor)
            and parse_version(pd.__version__) < parse_version("1.0.0")
        )
        else nullcontext()
    )
    data = {"b": [4, 5, None], "a": [1, 2, 3]}
    with context:
        result = (
            nw.from_native(constructor(data))
            .group_by("b")
            .agg(nw.len(), nw.col("a").min())
            .sort("a")
            .with_columns(nw.col("b").cast(nw.Float64))
        )
        expected = {"b": [4.0, 5, float("nan")], "len": [1, 1, 1], "a": [1, 2, 3]}
        compare_dicts(result, expected)
