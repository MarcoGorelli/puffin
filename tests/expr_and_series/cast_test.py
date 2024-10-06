from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pandas as pd
import pyarrow as pa
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version
from tests.utils import Constructor
from tests.utils import compare_dicts
from tests.utils import is_windows

data = {
    "a": [1],
    "b": [1],
    "c": [1],
    "d": [1],
    "e": [1],
    "f": [1],
    "g": [1],
    "h": [1],
    "i": [1],
    "j": [1],
    "k": ["1"],
    "l": [1],
    "m": [True],
    "n": [True],
    "o": ["a"],
    "p": [1],
}
schema = {
    "a": nw.Int64,
    "b": nw.Int32,
    "c": nw.Int16,
    "d": nw.Int8,
    "e": nw.UInt64,
    "f": nw.UInt32,
    "g": nw.UInt16,
    "h": nw.UInt8,
    "i": nw.Float64,
    "j": nw.Float32,
    "k": nw.String,
    "l": nw.Datetime,
    "m": nw.Boolean,
    "n": nw.Boolean,
    "o": nw.Categorical,
    "p": nw.Int64,
}


@pytest.mark.filterwarnings("ignore:casting period[M] values to int64:FutureWarning")
def test_cast(constructor: Constructor, request: pytest.FixtureRequest) -> None:
    if "pyarrow_table_constructor" in str(constructor) and parse_version(
        pa.__version__
    ) <= (15,):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)
    if "modin" in str(constructor):
        # TODO(unassigned): in modin, we end up with `'<U0'` dtype
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor(data)).select(
        nw.col(key).cast(value) for key, value in schema.items()
    )
    result = df.select(
        nw.col("a").cast(nw.Int32),
        nw.col("b").cast(nw.Int16),
        nw.col("c").cast(nw.Int8),
        nw.col("d").cast(nw.Int64),
        nw.col("e").cast(nw.UInt32),
        nw.col("f").cast(nw.UInt16),
        nw.col("g").cast(nw.UInt8),
        nw.col("h").cast(nw.UInt64),
        nw.col("i").cast(nw.Float32),
        nw.col("j").cast(nw.Float64),
        nw.col("k").cast(nw.String),
        nw.col("l").cast(nw.Datetime),
        nw.col("m").cast(nw.Int8),
        nw.col("n").cast(nw.Int8),
        nw.col("o").cast(nw.String),
        nw.col("p").cast(nw.Duration),
    )
    expected = {
        "a": nw.Int32,
        "b": nw.Int16,
        "c": nw.Int8,
        "d": nw.Int64,
        "e": nw.UInt32,
        "f": nw.UInt16,
        "g": nw.UInt8,
        "h": nw.UInt64,
        "i": nw.Float32,
        "j": nw.Float64,
        "k": nw.String,
        "l": nw.Datetime,
        "m": nw.Int8,
        "n": nw.Int8,
        "o": nw.String,
        "p": nw.Duration,
    }
    assert dict(result.collect_schema()) == expected


def test_cast_series(constructor: Constructor, request: pytest.FixtureRequest) -> None:
    if "pyarrow_table_constructor" in str(constructor) and parse_version(
        pa.__version__
    ) <= (15,):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)
    if "modin" in str(constructor):
        # TODO(unassigned): in modin, we end up with `'<U0'` dtype
        request.applymarker(pytest.mark.xfail)
    df = (
        nw.from_native(constructor(data))
        .select(nw.col(key).cast(value) for key, value in schema.items())
        .lazy()
        .collect()
    )

    expected = {
        "a": nw.Int32,
        "b": nw.Int16,
        "c": nw.Int8,
        "d": nw.Int64,
        "e": nw.UInt32,
        "f": nw.UInt16,
        "g": nw.UInt8,
        "h": nw.UInt64,
        "i": nw.Float32,
        "j": nw.Float64,
        "k": nw.String,
        "l": nw.Datetime,
        "m": nw.Int8,
        "n": nw.Int8,
        "o": nw.String,
        "p": nw.Duration,
    }
    result = df.select(
        df["a"].cast(nw.Int32),
        df["b"].cast(nw.Int16),
        df["c"].cast(nw.Int8),
        df["d"].cast(nw.Int64),
        df["e"].cast(nw.UInt32),
        df["f"].cast(nw.UInt16),
        df["g"].cast(nw.UInt8),
        df["h"].cast(nw.UInt64),
        df["i"].cast(nw.Float32),
        df["j"].cast(nw.Float64),
        df["k"].cast(nw.String),
        df["l"].cast(nw.Datetime),
        df["m"].cast(nw.Int8),
        df["n"].cast(nw.Int8),
        df["o"].cast(nw.String),
        df["p"].cast(nw.Duration),
    )
    assert result.schema == expected


@pytest.mark.skipif(
    parse_version(pd.__version__) < parse_version("1.0.0"),
    reason="too old for convert_dtypes",
)
def test_cast_string() -> None:
    s_pd = pd.Series([1, 2]).convert_dtypes()
    s = nw.from_native(s_pd, series_only=True)
    s = s.cast(nw.String)
    result = nw.to_native(s)
    assert str(result.dtype) in ("string", "object", "dtype('O')")


def test_cast_raises_for_unknown_dtype(
    constructor: Constructor, request: pytest.FixtureRequest
) -> None:
    if "pyarrow_table_constructor" in str(constructor) and parse_version(
        pa.__version__
    ) <= (15,):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)
    if "polars" in str(constructor):
        request.applymarker(pytest.mark.xfail)

    df = nw.from_native(constructor(data)).select(
        nw.col(key).cast(value) for key, value in schema.items()
    )

    class Banana:
        pass

    with pytest.raises(AssertionError, match=r"Unknown dtype"):
        df.select(nw.col("a").cast(Banana))


def test_cast_datetime_tz_aware(
    constructor: Constructor, request: pytest.FixtureRequest
) -> None:
    if (
        "dask" in str(constructor)
        or "cudf" in str(constructor)  # https://github.com/rapidsai/cudf/issues/16973
        or ("pyarrow_table" in str(constructor) and is_windows())
    ):
        request.applymarker(pytest.mark.xfail)

    data = {
        "date": [
            datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i)
            for i in range(3)
        ]
    }
    expected = {
        "date": ["2024-01-01 01:00:00", "2024-01-02 01:00:00", "2024-01-03 01:00:00"]
    }

    df = nw.from_native(constructor(data))
    result = df.select(
        nw.col("date")
        .cast(nw.Datetime("ms", time_zone="Europe/Rome"))
        .cast(nw.String())
        .str.slice(offset=0, length=19)
    )
    compare_dicts(result, expected)
