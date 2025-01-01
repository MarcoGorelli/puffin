from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.conftest import dask_lazy_p2_constructor
from tests.conftest import pandas_constructor
from tests.utils import Constructor
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data

NON_NULLABLE_CONSTRUCTORS = [pandas_constructor, dask_lazy_p2_constructor]


def test_nan(constructor: Constructor) -> None:
    data_na = {"int": [0, 1, None]}
    df = nw.from_native(constructor(data_na)).with_columns(
        float=nw.col("int").cast(nw.Float64), float_na=nw.col("int") / nw.col("int")
    )
    result = df.select(
        int=nw.col("int").is_nan(),
        float=nw.col("float").is_nan(),
        float_na=nw.col("float_na").is_nan(),
    )

    expected: dict[str, list[Any]]
    if any(constructor is c for c in NON_NULLABLE_CONSTRUCTORS):
        # Null values are coerced to NaN for non-nullable datatypes
        expected = {
            "int": [False, False, True],
            "float": [False, False, True],
            "float_na": [True, False, True],
        }
    else:
        # Null are preserved and should be differentiated for nullable datatypes
        expected = {
            "int": [False, False, None],
            "float": [False, False, None],
            "float_na": [True, False, None],
        }

    assert_equal_data(result, expected)


def test_nan_series(constructor_eager: ConstructorEager) -> None:
    data_na = {"int": [0, 1, None]}
    df = nw.from_native(constructor_eager(data_na), eager_only=True).with_columns(
        float=nw.col("int").cast(nw.Float64), float_na=nw.col("int") / nw.col("int")
    )

    result = {
        "int": df["int"].is_nan(),
        "float": df["float"].is_nan(),
        "float_na": df["float_na"].is_nan(),
    }
    expected: dict[str, list[Any]]
    if any(constructor_eager is c for c in NON_NULLABLE_CONSTRUCTORS):
        # Null values are coerced to NaN for non-nullable datatypes
        expected = {
            "int": [False, False, True],
            "float": [False, False, True],
            "float_na": [True, False, True],
        }
    else:
        # Null are preserved and should be differentiated for nullable datatypes
        expected = {
            "int": [False, False, None],
            "float": [False, False, None],
            "float_na": [True, False, None],
        }

    assert_equal_data(result, expected)


def test_nan_non_float(constructor: Constructor) -> None:
    from polars.exceptions import InvalidOperationError as PlInvalidOperationError
    from pyarrow.lib import ArrowNotImplementedError

    from narwhals.exceptions import InvalidOperationError as NwInvalidOperationError

    data = {"a": ["x", "y"]}
    df = nw.from_native(constructor(data))

    if "polars" in str(constructor):
        with pytest.raises(PlInvalidOperationError):
            df.select(nw.col("a").is_nan()).lazy().collect()

    elif "dask" in str(constructor) or "pandas" in str(constructor):
        with pytest.raises(NwInvalidOperationError):
            df.select(nw.col("a").is_nan())

    elif "pyarrow" in str(constructor):
        with pytest.raises(ArrowNotImplementedError):
            df.select(nw.col("a").is_nan())


def test_nan_non_float_series(constructor_eager: ConstructorEager) -> None:
    from polars.exceptions import InvalidOperationError as PlInvalidOperationError
    from pyarrow.lib import ArrowNotImplementedError

    from narwhals.exceptions import InvalidOperationError as NwInvalidOperationError

    data = {"a": ["x", "y"]}
    df = nw.from_native(constructor_eager(data), eager_only=True)

    if "polars" in str(constructor_eager):
        with pytest.raises(PlInvalidOperationError):
            df["a"].is_nan()

    elif "dask" in str(constructor_eager) or "pandas" in str(constructor_eager):
        with pytest.raises(NwInvalidOperationError):
            df["a"].is_nan()

    elif "pyarrow" in str(constructor_eager):
        with pytest.raises(ArrowNotImplementedError):
            df["a"].is_nan()