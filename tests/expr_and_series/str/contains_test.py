from typing import Any

import pandas as pd
import polars as pl

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {"pets": ["cat", "dog", "rabbit and parrot", "dove"]}

df_pandas = pd.DataFrame(data)
df_polars = pl.DataFrame(data)


def test_contains(constructor: Any) -> None:
    df = nw.from_native(constructor(data), eager_only=True)
    result = df.with_columns(
        case_insensitive_match=nw.col("pets").str.contains("(?i)parrot|Dove")
    )
    expected = {
        "pets": ["cat", "dog", "rabbit and parrot", "dove"],
        "case_insensitive_match": [False, False, True, True],
    }
    compare_dicts(result, expected)
    result = df.with_columns(
        case_insensitive_match=df["pets"].str.contains("(?i)parrot|Dove")
    )
    compare_dicts(result, expected)
