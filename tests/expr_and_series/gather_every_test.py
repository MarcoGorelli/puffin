from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = {"a": list(range(10))}


@pytest.mark.parametrize("n", [1, 2, 3])
@pytest.mark.parametrize("offset", [1, 2, 3])
def test_gather_every_expr(constructor: Any, n: int, offset: int, request: Any) -> None:
    if "dask" in str(constructor):
        request.applymarker(pytest.mark.xfail)
    df = nw.from_native(constructor(data))

    result = df.select(nw.col("a").gather_every(n=n, offset=offset))
    expected = {"a": data["a"][offset::n]}

    compare_dicts(result, expected)


@pytest.mark.parametrize("n", [1, 2, 3])
@pytest.mark.parametrize("offset", [1, 2, 3])
def test_gather_every_series(constructor_eager: Any, n: int, offset: int) -> None:
    series = nw.from_native(constructor_eager(data), eager_only=True)["a"]

    result = series.gather_every(n=n, offset=offset)
    expected = data["a"][offset::n]

    assert result.to_list() == expected
