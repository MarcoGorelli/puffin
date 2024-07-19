from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import Any

import polars as pl
import pytest

import narwhals as nw
from tests.utils import compare_dicts

data = {"foo": [1, 2, 3], "BAR": [4, 5, 6]}


def test_to_uppercase(constructor_with_lazy: Any) -> None:
    df = nw.from_native(constructor_with_lazy(data))
    result = df.select((nw.col("foo", "BAR") * 2).name.to_uppercase())
    expected = {k.upper(): [e * 2 for e in v] for k, v in data.items()}
    compare_dicts(result, expected)


def test_to_uppercase_after_alias(constructor_with_lazy: Any) -> None:
    df = nw.from_native(constructor_with_lazy(data))
    result = df.select((nw.col("foo")).alias("alias_for_foo").name.to_uppercase())
    expected = {"FOO": data["foo"]}
    compare_dicts(result, expected)


def test_to_uppercase_raise_anonymous(constructor: Any) -> None:
    df_raw = constructor(data)
    df = nw.from_native(df_raw)

    context = (
        does_not_raise()
        if isinstance(df_raw, (pl.LazyFrame, pl.DataFrame))
        else pytest.raises(
            ValueError,
            match="Anonymous expressions are not supported in `.name.to_uppercase`.",
        )
    )

    with context:
        df.select(nw.all().name.to_uppercase())
