from typing import Any

import narwhals as nw
import narwhals.stable.v1 as nw_v1


def test_lazy(constructor_eager: Any) -> None:
    df = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)
    result = df.lazy()
    assert isinstance(result, nw.LazyFrame)
    df = nw_v1.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)
    result = df.lazy()
    assert isinstance(result, nw_v1.LazyFrame)
