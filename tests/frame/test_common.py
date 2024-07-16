from __future__ import annotations

import re
import warnings
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import narwhals.stable.v1 as nw
from narwhals.functions import _get_deps_info
from narwhals.functions import _get_sys_info
from narwhals.functions import show_versions
from tests.utils import compare_dicts

data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
data_na = {"a": [None, 3, 2], "b": [4, 4, 6], "z": [7.0, None, 9]}
data_right = {"c": [6, 12, -1], "d": [0, -4, 2]}


def test_empty_select(constructor: Any) -> None:
    result = nw.from_native(constructor({"a": [1, 2, 3]}), eager_only=True).select()
    assert result.shape == (0, 0)


def test_std(constructor: Any) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(
        nw.col("a").std().alias("a_ddof_default"),
        nw.col("a").std(ddof=1).alias("a_ddof_1"),
        nw.col("a").std(ddof=0).alias("a_ddof_0"),
        nw.col("b").std(ddof=2).alias("b_ddof_2"),
        nw.col("z").std(ddof=0).alias("z_ddof_0"),
    )
    expected = {
        "a_ddof_default": [1.0],
        "a_ddof_1": [1.0],
        "a_ddof_0": [0.816497],
        "b_ddof_2": [1.632993],
        "z_ddof_0": [0.816497],
    }
    compare_dicts(result, expected)


@pytest.mark.filterwarnings("ignore:Determining|Resolving.*")
def test_schema(constructor_with_lazy: Any) -> None:
    df = nw.from_native(
        constructor_with_lazy({"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.1, 8, 9]})
    )
    result = df.schema
    expected = {"a": nw.Int64, "b": nw.Int64, "z": nw.Float64}

    result = df.schema
    assert result == expected
    result = df.lazy().collect().schema
    assert result == expected


def test_collect_schema(constructor_with_lazy: Any) -> None:
    df = nw.from_native(
        constructor_with_lazy({"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.1, 8, 9]})
    )
    expected = {"a": nw.Int64, "b": nw.Int64, "z": nw.Float64}

    result = df.collect_schema()
    assert result == expected
    result = df.lazy().collect().collect_schema()
    assert result == expected


@pytest.mark.filterwarnings("ignore:Determining|Resolving.*")
def test_columns(constructor_with_lazy: Any) -> None:
    df = nw.from_native(constructor_with_lazy(data))
    result = df.columns
    expected = ["a", "b", "z"]
    assert result == expected


def test_expr_binary(request: Any, constructor: Any) -> None:
    if (
        "pyarrow_table" in str(constructor)
        or "pandas_pyarrow"
        in str(constructor)  # pandas pyarrow raises NotImplementedError for __mod__
    ):
        request.applymarker(pytest.mark.xfail)
    df_raw = constructor(data)
    result = nw.from_native(df_raw).with_columns(
        a=(1 + 3 * nw.col("a")) * (1 / nw.col("a")),
        b=nw.col("z") / (2 - nw.col("b")),
        c=nw.col("a") + nw.col("b") / 2,
        d=nw.col("a") - nw.col("b"),
        e=((nw.col("a") > nw.col("b")) & (nw.col("a") >= nw.col("z"))).cast(nw.Int64),
        f=(
            (nw.col("a") < nw.col("b"))
            | (nw.col("a") <= nw.col("z"))
            | (nw.col("a") == 1)
        ).cast(nw.Int64),
        g=nw.col("a") != 1,
        h=(False & (nw.col("a") != 1)),
        i=(False | (nw.col("a") != 1)),
        j=2 ** nw.col("a"),
        k=2 // nw.col("a"),
        l=nw.col("a") // 2,
        m=nw.col("a") ** 2,
        n=nw.col("a") % 2,
        o=2 % nw.col("a"),
    )
    result_native = nw.to_native(result)
    expected = {
        "a": [4, 3.333333, 3.5],
        "b": [-3.5, -4.0, -2.25],
        "z": [7.0, 8.0, 9.0],
        "c": [3, 5, 5],
        "d": [-3, -1, -4],
        "e": [0, 0, 0],
        "f": [1, 1, 1],
        "g": [False, True, True],
        "h": [False, False, False],
        "i": [False, True, True],
        "j": [2, 8, 4],
        "k": [2, 0, 1],
        "l": [0, 1, 1],
        "m": [1, 9, 4],
        "n": [1, 1, 0],
        "o": [0, 2, 0],
    }
    compare_dicts(result_native, expected)


def test_expr_transform(request: Any, constructor: Any) -> None:
    if "pyarrow_table" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data))
    result = df.with_columns(a=nw.col("a").is_between(-1, 1), b=nw.col("b").is_in([4, 5]))
    expected = {"a": [True, False, False], "b": [True, True, False], "z": [7, 8, 9]}
    compare_dicts(result, expected)


def test_expr_min_max(request: Any, constructor: Any) -> None:
    if "pyarrow_table" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data))
    result_min = df.select(nw.min("a", "b", "z"))
    result_max = df.select(nw.max("a", "b", "z"))
    expected_min = {"a": [1], "b": [4], "z": [7]}
    expected_max = {"a": [3], "b": [6], "z": [9]}
    compare_dicts(result_min, expected_min)
    compare_dicts(result_max, expected_max)


def test_expr_na(constructor_with_lazy: Any) -> None:
    df = nw.from_native(constructor_with_lazy(data_na)).lazy()
    result_nna = df.filter((~nw.col("a").is_null()) & (~df.collect()["z"].is_null()))
    expected = {"a": [2], "b": [6], "z": [9]}
    compare_dicts(result_nna, expected)


def test_drop_nulls(request: Any, constructor_with_lazy: Any) -> None:
    if "pyarrow_table" in str(constructor_with_lazy):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_with_lazy(data_na)).lazy()

    result = df.select(nw.col("a").drop_nulls())
    expected = {"a": [3, 2]}
    compare_dicts(result, expected)

    result = df.select(df.collect()["a"].drop_nulls())
    expected = {"a": [3, 2]}
    compare_dicts(result, expected)


@pytest.mark.parametrize(
    ("drop", "left"),
    [
        (["a"], ["b", "z"]),
        (["a", "b"], ["z"]),
    ],
)
def test_drop(constructor: Any, drop: list[str], left: list[str]) -> None:
    df = nw.from_native(constructor(data))
    assert df.drop(drop).columns == left
    assert df.drop(*drop).columns == left


def test_concat_horizontal(constructor_with_lazy: Any) -> None:
    df_left = nw.from_native(constructor_with_lazy(data))
    df_right = nw.from_native(constructor_with_lazy(data_right))
    result = nw.concat([df_left, df_right], how="horizontal")
    expected = {
        "a": [1, 3, 2],
        "b": [4, 4, 6],
        "z": [7.0, 8, 9],
        "c": [6, 12, -1],
        "d": [0, -4, 2],
    }
    compare_dicts(result, expected)

    with pytest.raises(ValueError, match="No items"):
        nw.concat([])


def test_concat_vertical(constructor_with_lazy: Any) -> None:
    df_left = (
        nw.from_native(constructor_with_lazy(data))
        .rename({"a": "c", "b": "d"})
        .drop("z")
        .lazy()
    )
    df_right = nw.from_native(constructor_with_lazy(data_right)).lazy()

    result = nw.concat([df_left, df_right], how="vertical")
    expected = {"c": [1, 3, 2, 6, 12, -1], "d": [4, 4, 6, 0, -4, 2]}
    compare_dicts(result, expected)

    with pytest.raises(ValueError, match="No items"):
        nw.concat([], how="vertical")

    with pytest.raises((Exception, TypeError), match="unable to vstack"):
        nw.concat([df_left, df_right.rename({"d": "i"})], how="vertical").collect()


def test_lazy(constructor: Any) -> None:
    df = nw.from_native(constructor({"a": [1, 2, 3]}), eager_only=True)
    result = df.lazy()
    assert isinstance(result, nw.LazyFrame)


def test_invalid() -> None:
    df = nw.from_native(pa.table({"a": [1, 2], "b": [3, 4]}))
    with pytest.raises(ValueError, match="Multi-output"):
        df.select(nw.all() + nw.all())
    df = nw.from_native(pd.DataFrame(data))
    with pytest.raises(ValueError, match="Multi-output"):
        df.select(nw.all() + nw.all())
    with pytest.raises(TypeError, match="Perhaps you:"):
        df.select([pl.col("a")])  # type: ignore[list-item]
    with pytest.raises(TypeError, match="Perhaps you:"):
        df.select([nw.col("a").cast(pl.Int64)])


@pytest.mark.parametrize("df_raw", [pd.DataFrame(data)])
def test_reindex(df_raw: Any) -> None:
    df = nw.from_native(df_raw, eager_only=True)
    result = df.select("b", df["a"].sort(descending=True))
    expected = {"b": [4, 4, 6], "a": [3, 2, 1]}
    compare_dicts(result, expected)
    result = df.select("b", nw.col("a").sort(descending=True))
    compare_dicts(result, expected)

    s = df["a"]
    result_s = s > s.sort()
    assert not result_s[0]
    assert result_s[1]
    assert not result_s[2]
    result = df.with_columns(s.sort())
    expected = {"a": [1, 2, 3], "b": [4, 4, 6], "z": [7.0, 8.0, 9.0]}  # type: ignore[list-item]
    compare_dicts(result, expected)
    with pytest.raises(ValueError, match="Multi-output expressions are not supported"):
        nw.to_native(df.with_columns(nw.all() + nw.all()))


@pytest.mark.parametrize(
    ("c_left", "c_right"),
    [(pd.DataFrame, pl.DataFrame), (pa.table, pd.DataFrame)],
)
def test_library(c_left: Any, c_right: Any) -> None:
    df_left = nw.from_native(c_left(data)).lazy()
    df_right = nw.from_native(c_right(data)).lazy()
    with pytest.raises(
        NotImplementedError, match="Cross-library comparisons aren't supported"
    ):
        nw.concat([df_left, df_right], how="horizontal")
    with pytest.raises(
        NotImplementedError, match="Cross-library comparisons aren't supported"
    ):
        nw.concat([df_left, df_right], how="vertical")
    with pytest.raises(
        NotImplementedError, match="Cross-library comparisons aren't supported"
    ):
        df_left.join(df_right, left_on=["a"], right_on=["a"], how="inner")


@pytest.mark.parametrize(
    ("row", "column", "expected"),
    [(0, 2, 7), (1, "z", 8)],
)
def test_item(
    constructor: Any, row: int | None, column: int | str | None, expected: Any
) -> None:
    df = nw.from_native(constructor(data), eager_only=True)
    assert df.item(row, column) == expected
    assert df.select("a").head(1).item() == 1


@pytest.mark.parametrize(
    ("row", "column", "err_msg"),
    [
        (0, None, re.escape("cannot call `.item()` with only one of `row` or `column`")),
        (None, 0, re.escape("cannot call `.item()` with only one of `row` or `column`")),
        (
            None,
            None,
            re.escape("can only call `.item()` if the dataframe is of shape (1, 1)"),
        ),
    ],
)
def test_item_value_error(
    constructor: Any, row: int | None, column: int | str | None, err_msg: str
) -> None:
    with pytest.raises(ValueError, match=err_msg):
        nw.from_native(constructor(data), eager_only=True).item(row, column)


def test_with_columns_order(constructor: Any) -> None:
    df = nw.from_native(constructor(data))
    result = df.with_columns(nw.col("a") + 1, d=nw.col("a") - 1)
    assert result.columns == ["a", "b", "z", "d"]
    expected = {"a": [2, 4, 3], "b": [4, 4, 6], "z": [7.0, 8, 9], "d": [0, 2, 1]}
    compare_dicts(result, expected)


def test_with_columns_order_single_row(constructor: Any) -> None:
    df = nw.from_native(constructor(data)[:1])
    assert len(df) == 1
    result = df.with_columns(nw.col("a") + 1, d=nw.col("a") - 1)
    assert result.columns == ["a", "b", "z", "d"]
    expected = {"a": [2], "b": [4], "z": [7.0], "d": [0]}
    compare_dicts(result, expected)


def test_get_sys_info() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        show_versions()
        sys_info = _get_sys_info()

    assert "python" in sys_info
    assert "executable" in sys_info
    assert "machine" in sys_info


def test_get_deps_info() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        show_versions()
        deps_info = _get_deps_info()

    assert "narwhals" in deps_info
    assert "pandas" in deps_info
    assert "polars" in deps_info
    assert "cudf" in deps_info
    assert "modin" in deps_info
    assert "pyarrow" in deps_info
    assert "numpy" in deps_info


def test_show_versions(capsys: Any) -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        show_versions()
        out, _ = capsys.readouterr()

    assert "python" in out
    assert "machine" in out
    assert "pandas" in out
    assert "polars" in out
