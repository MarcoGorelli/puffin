from __future__ import annotations

import narwhals.stable.v1 as nw
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data


def test_head(constructor: ConstructorEager) -> None:
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    expected = {"a": [1, 3], "b": [4, 4], "z": [7.0, 8.0]}

    df_raw = constructor(data)
    df = nw.from_native(df_raw)

    result = df.head(2)
    assert_equal_data(result, expected)

    result = df.head(2)
    assert_equal_data(result, expected)

    # negative indices not allowed for lazyframes
    result = df.lazy().collect().head(-1)
    assert_equal_data(result, expected)
