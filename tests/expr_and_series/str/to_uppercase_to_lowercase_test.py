from __future__ import annotations

from typing import Any

import pyarrow as pa
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version
from tests.utils import Constructor
from tests.utils import compare_dicts


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"a": ["foo", "bar"]}, {"a": ["FOO", "BAR"]}),
        (
            {
                "a": [
                    "special case ß",
                    "ςpecial caσe",  # noqa: RUF001
                ]
            },
            {"a": ["SPECIAL CASE SS", "ΣPECIAL CAΣE"]},
        ),
    ],
)
def test_str_to_uppercase(
    constructor: Constructor,
    data: dict[str, list[str]],
    expected: dict[str, list[str]],
    request: pytest.FixtureRequest,
) -> None:
    df = nw.from_native(constructor(data))
    result_frame = df.select(nw.col("a").str.to_uppercase())

    if any("ß" in s for value in data.values() for s in value) & (
        constructor.__name__
        in (
            "pandas_pyarrow_constructor",
            "pyarrow_table_constructor",
            "modin_constructor",
        )
        or ("dask" in str(constructor) and parse_version(pa.__version__) >= (12,))
    ):
        # We are marking it xfail for these conditions above
        # since the pyarrow backend will convert
        # smaller cap 'ß' to upper cap 'ẞ' instead of 'SS'
        request.applymarker(pytest.mark.xfail)

    compare_dicts(result_frame, expected)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"a": ["foo", "bar"]}, {"a": ["FOO", "BAR"]}),
        (
            {
                "a": [
                    "special case ß",
                    "ςpecial caσe",  # noqa: RUF001
                ]
            },
            {"a": ["SPECIAL CASE SS", "ΣPECIAL CAΣE"]},
        ),
    ],
)
def test_str_to_uppercase_series(
    constructor_eager: Any,
    data: dict[str, list[str]],
    expected: dict[str, list[str]],
    request: pytest.FixtureRequest,
) -> None:
    df = nw.from_native(constructor_eager(data), eager_only=True)

    if any("ß" in s for value in data.values() for s in value) & (
        constructor_eager.__name__
        not in (
            "pandas_constructor",
            "pandas_nullable_constructor",
            "polars_eager_constructor",
            "cudf_constructor",
        )
    ):
        # We are marking it xfail for these conditions above
        # since the pyarrow backend will convert
        # smaller cap 'ß' to upper cap 'ẞ' instead of 'SS'
        request.applymarker(pytest.mark.xfail)

    result_series = df["a"].str.to_uppercase()
    compare_dicts({"a": result_series}, expected)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"a": ["FOO", "BAR"]}, {"a": ["foo", "bar"]}),
        (
            {"a": ["SPECIAL CASE ß", "ΣPECIAL CAΣE"]},
            {
                "a": [
                    "special case ß",
                    "σpecial caσe",  # noqa: RUF001
                ]
            },
        ),
    ],
)
def test_str_to_lowercase(
    constructor: Constructor,
    data: dict[str, list[str]],
    expected: dict[str, list[str]],
) -> None:
    df = nw.from_native(constructor(data))
    result_frame = df.select(nw.col("a").str.to_lowercase())
    compare_dicts(result_frame, expected)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"a": ["FOO", "BAR"]}, {"a": ["foo", "bar"]}),
        (
            {"a": ["SPECIAL CASE ß", "ΣPECIAL CAΣE"]},
            {
                "a": [
                    "special case ß",
                    "σpecial caσe",  # noqa: RUF001
                ]
            },
        ),
    ],
)
def test_str_to_lowercase_series(
    constructor_eager: Any,
    data: dict[str, list[str]],
    expected: dict[str, list[str]],
) -> None:
    df = nw.from_native(constructor_eager(data), eager_only=True)

    result_series = df["a"].str.to_lowercase()
    compare_dicts({"a": result_series}, expected)
