from __future__ import annotations

import numpy as np
import pytest

import narwhals.stable.v1 as nw
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data


def test_array_dunder(
    request: pytest.FixtureRequest,
    constructor_eager: ConstructorEager,
    pyarrow_version: tuple[int, ...],
) -> None:
    if "pyarrow_table" in str(constructor_eager) and pyarrow_version < (
        16,
        0,
        0,
    ):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)
    result = df.__array__()
    np.testing.assert_array_equal(result, np.array([[1], [2], [3]], dtype="int64"))


def test_array_dunder_with_dtype(
    request: pytest.FixtureRequest,
    constructor_eager: ConstructorEager,
    pyarrow_version: tuple[int, ...],
) -> None:
    if "pyarrow_table" in str(constructor_eager) and pyarrow_version < (
        16,
        0,
        0,
    ):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)
    result = df.__array__(object)
    np.testing.assert_array_equal(result, np.array([[1], [2], [3]], dtype=object))


def test_array_dunder_with_copy(
    request: pytest.FixtureRequest,
    constructor_eager: ConstructorEager,
    pandas_version: tuple[int, ...],
    polars_version: tuple[int, ...],
    pyarrow_version: tuple[int, ...],
) -> None:
    if "pyarrow_table" in str(constructor_eager) and pyarrow_version < (
        16,
        0,
        0,
    ):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)
    if "polars" in str(constructor_eager) and polars_version < (
        0,
        20,
        28,
    ):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)
    result = df.__array__(copy=True)
    np.testing.assert_array_equal(result, np.array([[1], [2], [3]], dtype="int64"))
    if "pandas_constructor" in str(constructor_eager) and pandas_version < (3,):
        # If it's pandas, we know that `copy=False` definitely took effect.
        # So, let's check it!
        result = df.__array__(copy=False)
        np.testing.assert_array_equal(result, np.array([[1], [2], [3]], dtype="int64"))
        result[0, 0] = 999
        assert_equal_data(df, {"a": [999, 2, 3]})
