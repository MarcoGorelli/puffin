from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw
from narwhals.exceptions import InvalidOperationError
from tests.utils import Constructor
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data

data = {"a": [None, 1, 2, None, 4, 6, 11]}

kwargs_and_expected = {
    "x1": {"kwargs": {"window_size": 3}, "expected": [float("nan")] * 6 + [21]},
    "x2": {
        "kwargs": {"window_size": 3, "min_periods": 1},
        "expected": [float("nan"), 1.0, 3.0, 3.0, 6.0, 10.0, 21.0],
    },
    "x3": {
        "kwargs": {"window_size": 2, "min_periods": 1},
        "expected": [float("nan"), 1.0, 3.0, 2.0, 4.0, 10.0, 17.0],
    },
    "x4": {
        "kwargs": {"window_size": 5, "min_periods": 1, "center": True},
        "expected": [3.0, 3.0, 7.0, 13.0, 23.0, 21.0, 21.0],
    },
    "x5": {
        "kwargs": {"window_size": 4, "min_periods": 1, "center": True},
        "expected": [1.0, 3.0, 3.0, 7.0, 12.0, 21.0, 21.0],
    },
    "x6": {
        "kwargs": {"window_size": 0},
        "expected": [float("nan"), 1.0, 3.0, 3.0, 7.0, 13.0, 24.0],
    },
    # There are still some edge cases to take care of with nulls and min_periods=0:
    # "x7": {  # noqa: ERA001
    #     "kwargs": {"window_size": 2, "min_periods": 0},  # noqa: ERA001
    #     "expected": [float("nan"), 1.0, 3.0, 2.0, 4.0, 10.0, 17.0],  # noqa: ERA001
    # },
}


@pytest.mark.filterwarnings(
    "ignore:`Expr.rolling_sum` is being called from the stable API although considered an unstable feature."
)
def test_rolling_sum_expr(
    request: pytest.FixtureRequest, constructor: Constructor
) -> None:
    if "dask" in str(constructor):
        # TODO(FBruzzesi): Dask is raising the following error:
        # NotImplementedError: Partition size is less than overlapping window size.
        # Try using ``df.repartition`` to increase the partition size.
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data))
    result = df.select(
        **{
            name: nw.col("a").rolling_sum(**values["kwargs"])  # type: ignore[arg-type]
            for name, values in kwargs_and_expected.items()
        }
    )
    expected = {name: values["expected"] for name, values in kwargs_and_expected.items()}

    assert_equal_data(result, expected)


@pytest.mark.filterwarnings(
    "ignore:`Series.rolling_sum` is being called from the stable API although considered an unstable feature."
)
def test_rolling_sum_series(constructor_eager: ConstructorEager) -> None:
    df = nw.from_native(constructor_eager(data), eager_only=True)

    result = df.select(
        **{
            name: df["a"].rolling_sum(**values["kwargs"])  # type: ignore[arg-type]
            for name, values in kwargs_and_expected.items()
        }
    )
    expected = {name: values["expected"] for name, values in kwargs_and_expected.items()}
    assert_equal_data(result, expected)


@pytest.mark.filterwarnings(
    "ignore:`Expr.rolling_sum` is being called from the stable API although considered an unstable feature."
)
@pytest.mark.parametrize(
    ("window_size", "min_periods", "context"),
    [
        (
            -1,
            None,
            pytest.raises(
                ValueError, match="window_size should be greater or equal than 0"
            ),
        ),
        (
            4.2,
            None,
            pytest.raises(
                TypeError,
                match="argument 'window_size': 'float' object cannot be interpreted as an integer",
            ),
        ),
        (
            2,
            -1,
            pytest.raises(
                ValueError, match="min_periods should be greater or equal than 0"
            ),
        ),
        (
            2,
            4.2,
            pytest.raises(
                TypeError,
                match="argument 'min_periods': 'float' object cannot be interpreted as an integer",
            ),
        ),
        (
            1,
            2,
            pytest.raises(
                InvalidOperationError,
                match="`min_periods` should be less or equal than `window_size`",
            ),
        ),
    ],
)
def test_rolling_sum_expr_invalid_params(
    constructor: Constructor, window_size: int, min_periods: int | None, context: Any
) -> None:
    df = nw.from_native(constructor(data))

    with context:
        df.select(
            nw.col("a").rolling_sum(window_size=window_size, min_periods=min_periods)
        )


@pytest.mark.filterwarnings(
    "ignore:`Series.rolling_sum` is being called from the stable API although considered an unstable feature."
)
@pytest.mark.parametrize(
    ("window_size", "min_periods", "context"),
    [
        (
            -1,
            None,
            pytest.raises(
                ValueError, match="window_size should be greater or equal than 0"
            ),
        ),
        (
            4.2,
            None,
            pytest.raises(
                TypeError,
                match="argument 'window_size': 'float' object cannot be interpreted as an integer",
            ),
        ),
        (
            2,
            -1,
            pytest.raises(
                ValueError, match="min_periods should be greater or equal than 0"
            ),
        ),
        (
            2,
            4.2,
            pytest.raises(
                TypeError,
                match="argument 'min_periods': 'float' object cannot be interpreted as an integer",
            ),
        ),
        (
            1,
            2,
            pytest.raises(
                InvalidOperationError,
                match="`min_periods` should be less or equal than `window_size`",
            ),
        ),
    ],
)
def test_rolling_sum_series_invalid_params(
    constructor_eager: ConstructorEager,
    window_size: int,
    min_periods: int | None,
    context: Any,
) -> None:
    df = nw.from_native(constructor_eager(data))

    with context:
        df["a"].rolling_sum(window_size=window_size, min_periods=min_periods)
