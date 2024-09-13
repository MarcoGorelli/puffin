from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts


def test_from_dict(constructor: Any, request: pytest.FixtureRequest) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor({"a": [1, 2, 3], "b": [4, 5, 6]}))
    native_namespace = nw.get_native_namespace(df)
    result = nw.from_dict({"c": [1, 2], "d": [5, 6]}, native_namespace=native_namespace)
    expected = {"c": [1, 2], "d": [5, 6]}
    compare_dicts(result, expected)
    assert isinstance(result, nw.DataFrame)


def test_from_dict_schema(constructor: Any, request: pytest.FixtureRequest) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    schema = {"c": nw.Int16(), "d": nw.Float32()}
    df = nw.from_native(constructor({"a": [1, 2, 3], "b": [4, 5, 6]}))
    native_namespace = nw.get_native_namespace(df)
    result = nw.from_dict(
        {"c": [1, 2], "d": [5, 6]},
        native_namespace=native_namespace,
        schema=schema,  # type: ignore[arg-type]
    )
    assert result.collect_schema() == schema


def test_from_dict_without_namespace(constructor: Any) -> None:
    df = nw.from_native(constructor({"a": [1, 2, 3], "b": [4, 5, 6]})).lazy().collect()
    result = nw.from_dict({"c": df["a"], "d": df["b"]})
    compare_dicts(result, {"c": [1, 2, 3], "d": [4, 5, 6]})


def test_from_dict_without_namespace_invalid(constructor: Any) -> None:
    df = nw.from_native(constructor({"a": [1, 2, 3], "b": [4, 5, 6]})).lazy().collect()
    with pytest.raises(TypeError, match="namespace"):
        nw.from_dict({"c": nw.to_native(df["a"]), "d": nw.to_native(df["b"])})


def test_from_dict_one_native_one_narwhals(constructor: Any) -> None:
    df = nw.from_native(constructor({"a": [1, 2, 3], "b": [4, 5, 6]})).lazy().collect()
    result = nw.from_dict({"c": nw.to_native(df["a"]), "d": df["b"]})
    expected = {"c": [1, 2, 3], "d": [4, 5, 6]}
    compare_dicts(result, expected)


def test_from_dict_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        nw.from_dict({})
