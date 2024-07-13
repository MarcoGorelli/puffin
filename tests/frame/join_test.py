from __future__ import annotations

import re
from typing import Any

import pandas as pd
import pytest

import narwhals.stable.v1 as nw
from narwhals._pandas_like.utils import Implementation
from tests.utils import compare_dicts


def test_inner_join_two_keys(constructor_with_pyarrow: Any) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df = nw.from_native(constructor_with_pyarrow(data), eager_only=True)
    df_right = df
    result = df.join(df_right, left_on=["a", "b"], right_on=["a", "b"], how="inner")
    expected = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9], "z_right": [7.0, 8, 9]}
    compare_dicts(result, expected)


def test_inner_join_single_key(constructor_with_pyarrow: Any) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df = nw.from_native(constructor_with_pyarrow(data), eager_only=True)
    df_right = df
    result = df.join(df_right, left_on="a", right_on="a", how="inner")
    expected = {
        "a": [1, 3, 2],
        "b": [4, 4, 6],
        "b_right": [4, 4, 6],
        "z": [7.0, 8, 9],
        "z_right": [7.0, 8, 9],
    }
    compare_dicts(result, expected)


def test_cross_join(constructor: Any) -> None:
    data = {"a": [1, 3, 2]}
    df = nw.from_native(constructor(data))
    result = df.join(df, how="cross")  # type: ignore[arg-type]

    expected = {"a": [1, 1, 1, 3, 3, 3, 2, 2, 2], "a_right": [1, 3, 2, 1, 3, 2, 1, 3, 2]}
    compare_dicts(result, expected)

    with pytest.raises(ValueError, match="Can not pass left_on, right_on for cross join"):
        df.join(df, how="cross", left_on="a")  # type: ignore[arg-type]


def test_cross_join_non_pandas() -> None:
    data = {"a": [1, 3, 2]}
    df = nw.from_native(pd.DataFrame(data))
    # HACK to force testing for a non-pandas codepath
    df._compliant_frame._implementation = Implementation.MODIN
    result = df.join(df, how="cross")  # type: ignore[arg-type]
    expected = {"a": [1, 1, 1, 3, 3, 3, 2, 2, 2], "a_right": [1, 3, 2, 1, 3, 2, 1, 3, 2]}
    compare_dicts(result, expected)


@pytest.mark.parametrize(
    ("join_key", "filter_expr", "expected"),
    [
        (["a", "b"], (nw.col("b") < 5), {"a": [2], "b": [6], "z": [9]}),
        (["b"], (nw.col("b") < 5), {"a": [2], "b": [6], "z": [9]}),
        (["b"], (nw.col("b") > 5), {"a": [1, 3], "b": [4, 4], "z": [7.0, 8.0]}),
    ],
)
def test_anti_join(
    constructor: Any,
    join_key: list[str],
    filter_expr: nw.Expr,
    expected: dict[str, list[Any]],
) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df = nw.from_native(constructor(data))
    other = df.filter(filter_expr)
    result = df.join(other, how="anti", left_on=join_key, right_on=join_key)  # type: ignore[arg-type]
    compare_dicts(result, expected)


@pytest.mark.parametrize(
    ("join_key", "filter_expr", "expected"),
    [
        (["a"], (nw.col("b") > 5), {"a": [2], "b": [6], "z": [9]}),
        (["b"], (nw.col("b") < 5), {"a": [1, 3], "b": [4, 4], "z": [7, 8]}),
        (["a", "b"], (nw.col("b") < 5), {"a": [1, 3], "b": [4, 4], "z": [7, 8]}),
    ],
)
def test_semi_join(
    constructor: Any,
    join_key: list[str],
    filter_expr: nw.Expr,
    expected: dict[str, list[Any]],
) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df = nw.from_native(constructor(data))
    other = df.filter(filter_expr)
    result = df.join(other, how="semi", left_on=join_key, right_on=join_key)  # type: ignore[arg-type]
    compare_dicts(result, expected)


@pytest.mark.parametrize("how", ["right", "full"])
def test_join_not_implemented(constructor: Any, how: str) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df = nw.from_native(constructor(data))

    with pytest.raises(
        NotImplementedError,
        match=re.escape(
            f"Only the following join stragies are supported: ('inner', 'left', 'cross', 'anti', 'semi'); found '{how}'."
        ),
    ):
        df.join(df, left_on="a", right_on="a", how=how)  # type: ignore[arg-type]


@pytest.mark.filterwarnings("ignore:the default coalesce behavior")
def test_left_join(constructor: Any) -> None:
    data_left = {"a": [1.0, 2, 3], "b": [4.0, 5, 6]}
    data_right = {"a": [1.0, 2, 3], "c": [4.0, 5, 7]}
    df_left = nw.from_native(constructor(data_left), eager_only=True)
    df_right = nw.from_native(constructor(data_right), eager_only=True)
    result = df_left.join(df_right, left_on="b", right_on="c", how="left").select(
        nw.all().fill_null(float("nan"))
    )
    expected = {"a": [1, 2, 3], "b": [4, 5, 6], "a_right": [1, 2, float("nan")]}
    compare_dicts(result, expected)


@pytest.mark.filterwarnings("ignore: the defaultcoalesce behavior")
def test_left_join_multiple_column(constructor: Any) -> None:
    data_left = {"a": [1, 2, 3], "b": [4, 5, 6]}
    data_right = {"a": [1, 2, 3], "c": [4, 5, 6]}
    df_left = nw.from_native(constructor(data_left), eager_only=True)
    df_right = nw.from_native(constructor(data_right), eager_only=True)
    result = df_left.join(df_right, left_on=["a", "b"], right_on=["a", "c"], how="left")
    expected = {"a": [1, 2, 3], "b": [4, 5, 6]}
    compare_dicts(result, expected)


@pytest.mark.filterwarnings("ignore: the defaultcoalesce behavior")
def test_left_join_overlapping_column(constructor: Any) -> None:
    data_left = {"a": [1, 2, 3], "b": [4, 5, 6], "d": [1, 4, 2]}
    data_right = {"a": [1, 2, 3], "c": [4, 5, 6], "d": [1, 4, 2]}
    df_left = nw.from_native(constructor(data_left), eager_only=True)
    df_right = nw.from_native(constructor(data_right), eager_only=True)
    result = df_left.join(df_right, left_on="b", right_on="c", how="left")
    expected: dict[str, list[Any]] = {
        "a": [1, 2, 3],
        "b": [4, 5, 6],
        "d": [1, 4, 2],
        "a_right": [1, 2, 3],
        "d_right": [1, 4, 2],
    }
    compare_dicts(result, expected)
    result = df_left.join(df_right, left_on="a", right_on="d", how="left").select(
        nw.all().fill_null(float("nan"))
    )
    expected = {
        "a": [1, 2, 3],
        "b": [4, 5, 6],
        "d": [1, 4, 2],
        "a_right": [1.0, 3.0, float("nan")],
        "c": [4.0, 6.0, float("nan")],
    }
    compare_dicts(result, expected)
