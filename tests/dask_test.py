"""
Dask support in Narwhals is still _very_ scant.

Start with a simple test file whilst we develop the basics.
Once we're a bit further along (say, we can at least evaluate
TPC-H Q1 with Dask), then we can integrate dask tests into
the main test suite.
"""

from __future__ import annotations

import sys
import warnings

import pandas as pd
import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

pytest.importorskip("dask")
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=pytest.PytestDeprecationWarning,
    )
    pytest.importorskip("dask_expr")


if sys.version_info < (3, 9):
    pytest.skip("Dask tests require Python 3.9+", allow_module_level=True)


def test_with_columns() -> None:
    import dask.dataframe as dd

    dfdd = dd.from_pandas(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))

    df = nw.from_native(dfdd)
    result = df.with_columns(
        nw.col("a") + 1,
        (nw.col("a") + nw.col("b").mean()).alias("c"),
        d=nw.col("a"),
        e=nw.col("a") + nw.col("b"),
        f=nw.col("b") - 1,
        g=nw.col("a") - nw.col("b"),
        h=nw.col("a") * 3,
        i=nw.col("a") * nw.col("b"),
    )
    compare_dicts(
        result,
        {
            "a": [2, 3, 4],
            "b": [4, 5, 6],
            "c": [6.0, 7.0, 8.0],
            "d": [1, 2, 3],
            "e": [5, 7, 9],
            "f": [3, 4, 5],
            "g": [-3, -3, -3],
            "h": [3, 6, 9],
            "i": [4, 10, 18],
        },
    )


def test_shift() -> None:
    import dask.dataframe as dd

    dfdd = dd.from_pandas(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    df = nw.from_native(dfdd)
    result = df.with_columns(nw.col("a").shift(1), nw.col("b").shift(-1))
    expected = {"a": [float("nan"), 1, 2], "b": [5, 6, float("nan")]}
    compare_dicts(result, expected)


def test_cum_sum() -> None:
    import dask.dataframe as dd

    dfdd = dd.from_pandas(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    df = nw.from_native(dfdd)
    result = df.with_columns(nw.col("a", "b").cum_sum())
    expected = {"a": [1, 3, 6], "b": [4, 9, 15]}
    compare_dicts(result, expected)


@pytest.mark.parametrize(
    ("closed", "expected"),
    [
        ("left", [True, True, True, False]),
        ("right", [False, True, True, True]),
        ("both", [True, True, True, True]),
        ("neither", [False, True, True, False]),
    ],
)
def test_is_between(closed: str, expected: list[bool]) -> None:
    import dask.dataframe as dd

    data = {
        "a": [1, 4, 2, 5],
    }
    dfdd = dd.from_pandas(pd.DataFrame(data))

    df = nw.from_native(dfdd)
    result = df.with_columns(nw.col("a").is_between(1, 5, closed=closed))
    expected_dict = {"a": expected}
    compare_dicts(result, expected_dict)


@pytest.mark.parametrize(
    ("prefix", "expected"),
    [
        ("fda", {"a": [True, False]}),
        ("edf", {"a": [False, True]}),
        ("asd", {"a": [False, False]}),
    ],
)
def test_starts_with(prefix: str, expected: dict[str, list[bool]]) -> None:
    import dask.dataframe as dd

    data = {"a": ["fdas", "edfas"]}
    dfdd = dd.from_pandas(pd.DataFrame(data))
    df = nw.from_native(dfdd)
    result = df.with_columns(nw.col("a").str.starts_with(prefix))

    compare_dicts(result, expected)
