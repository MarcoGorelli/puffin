from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts


@pytest.mark.filterwarnings(
    "ignore:.*all arguments of to_dict except for the argument:FutureWarning"
)
def test_to_dict(constructor_eager: Any) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "c": [7.0, 8, 9]}
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.to_dict(as_series=False)
    assert result == data


def test_to_dict_as_series(constructor_eager: Any) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "c": [7.0, 8, 9]}
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.to_dict(as_series=True)
    assert isinstance(result["a"], nw.Series)
    assert isinstance(result["b"], nw.Series)
    assert isinstance(result["c"], nw.Series)
    compare_dicts(result, data)
