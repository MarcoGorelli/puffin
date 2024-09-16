from __future__ import annotations

import pandas as pd
import pyarrow as pa
import pytest

import narwhals.stable.v1 as nw
from narwhals.selectors import all
from narwhals.selectors import boolean
from narwhals.selectors import by_dtype
from narwhals.selectors import categorical
from narwhals.selectors import numeric
from narwhals.selectors import string
from narwhals.utils import parse_version
from tests.utils import Constructor
from tests.utils import compare_dicts

data = {
    "a": [1, 1, 2],
    "b": ["a", "b", "c"],
    "c": [4.1, 5.0, 6.0],
    "d": [True, False, True],
}


def test_selectors(constructor: Constructor) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(by_dtype([nw.Int64, nw.Float64]) + 1)
    expected = {"a": [2, 2, 3], "c": [5.1, 6.0, 7.0]}
    compare_dicts(result, expected)


def test_numeric(constructor: Constructor) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(numeric() + 1)
    expected = {"a": [2, 2, 3], "c": [5.1, 6.0, 7.0]}
    compare_dicts(result, expected)


def test_boolean(constructor: Constructor) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(boolean())
    expected = {"d": [True, False, True]}
    compare_dicts(result, expected)


def test_string(constructor: Constructor, request: pytest.FixtureRequest) -> None:
    if "dask" in str(constructor) and parse_version(pa.__version__) < (12,):
        # Dask doesn't infer `'b'` as String for old PyArrow versions
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor(data))
    result = df.select(string())
    expected = {"b": ["a", "b", "c"]}
    compare_dicts(result, expected)


def test_categorical(request: pytest.FixtureRequest, constructor: Constructor) -> None:
    if "pyarrow_table_constructor" in str(constructor) and parse_version(
        pa.__version__
    ) <= (15,):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)
    expected = {"b": ["a", "b", "c"]}

    df = nw.from_native(constructor(data)).with_columns(nw.col("b").cast(nw.Categorical))
    result = df.select(categorical())
    compare_dicts(result, expected)


@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        (numeric() | boolean(), ["a", "c", "d"]),
        (numeric() & boolean(), []),
        (numeric() & by_dtype(nw.Int64), ["a"]),
        (numeric() | by_dtype(nw.Int64), ["a", "c"]),
        (~numeric(), ["b", "d"]),
        (boolean() & True, ["d"]),
        (boolean() | True, ["d"]),
        (numeric() - 1, ["a", "c"]),
        (all(), ["a", "b", "c", "d"]),
    ],
)
def test_set_ops(
    constructor: Constructor, selector: nw.selectors.Selector, expected: list[str]
) -> None:
    df = nw.from_native(constructor(data))
    result = df.select(selector).collect_schema().names()
    assert sorted(result) == expected


@pytest.mark.parametrize("invalid_constructor", [pd.DataFrame, pa.table])
def test_set_ops_invalid(invalid_constructor: Constructor) -> None:
    df = nw.from_native(invalid_constructor(data))
    with pytest.raises(NotImplementedError):
        df.select(1 - numeric())
    with pytest.raises(NotImplementedError):
        df.select(1 | numeric())
    with pytest.raises(NotImplementedError):
        df.select(1 & numeric())
