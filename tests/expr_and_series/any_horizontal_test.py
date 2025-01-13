from __future__ import annotations

from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data


@pytest.mark.parametrize("expr1", ["a", nw.col("a")])
@pytest.mark.parametrize("expr2", ["b", nw.col("b")])
def test_anyh(constructor: ConstructorEager, expr1: Any, expr2: Any) -> None:
    data = {
        "a": [False, False, True],
        "b": [False, True, True],
    }
    df = nw.from_native(constructor(data))
    result = df.select(any=nw.any_horizontal(expr1, expr2))

    expected = {"any": [False, True, True]}
    assert_equal_data(result, expected)


def test_anyh_all(constructor: ConstructorEager) -> None:
    data = {
        "a": [False, False, True],
        "b": [False, True, True],
    }
    df = nw.from_native(constructor(data))
    result = df.select(any=nw.any_horizontal(nw.all()))
    expected = {"any": [False, True, True]}
    assert_equal_data(result, expected)
    result = df.select(nw.any_horizontal(nw.all()))
    expected = {"a": [False, True, True]}
    assert_equal_data(result, expected)
