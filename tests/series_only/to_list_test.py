from __future__ import annotations

import narwhals.stable.v1 as nw
from tests.utils import ConstructorEager
from tests.utils import assert_equal_data

data = [1, 2, 3]


def test_to_list(constructor_eager: ConstructorEager) -> None:
    s = nw.from_native(constructor_eager({"a": data}), eager_only=True)["a"]
    assert_equal_data({"a": s.to_list()}, {"a": [1, 2, 3]})
