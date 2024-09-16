from typing import Any

import pandas as pd
import polars as pl
import pytest

import narwhals.stable.v1 as nw
from tests.utils import Constructor
from tests.utils import compare_dicts

data = {"pets": ["cat", "dog", "rabbit and parrot", "dove"]}

df_pandas = pd.DataFrame(data)
df_polars = pl.DataFrame(data)


def test_contains(constructor: Constructor, request: pytest.FixtureRequest) -> None:
    if "cudf" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data))
    result = df.with_columns(
        nw.col("pets").str.contains("(?i)parrot|Dove").alias("result")
    )
    expected = {
        "pets": ["cat", "dog", "rabbit and parrot", "dove"],
        "result": [False, False, True, True],
    }
    compare_dicts(result, expected)


def test_contains_series(constructor_eager: Any, request: pytest.FixtureRequest) -> None:
    if "cudf" in str(constructor_eager):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.with_columns(
        case_insensitive_match=df["pets"].str.contains("(?i)parrot|Dove")
    )
    expected = {
        "pets": ["cat", "dog", "rabbit and parrot", "dove"],
        "case_insensitive_match": [False, False, True, True],
    }
    compare_dicts(result, expected)
