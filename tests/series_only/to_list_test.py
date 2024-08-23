from typing import Any

import pytest

import narwhals.stable.v1 as nw
from tests.utils import compare_dicts

data = [1, 2, 3]


def test_to_list(constructor_eager: Any, request: Any) -> None:
    if "cudf" in str(constructor_eager):  # pragma: no cover
        request.applymarker(pytest.mark.xfail)
    s = nw.from_native(constructor_eager({"a": data}), eager_only=True)["a"]
    compare_dicts({"a": s.to_list()}, {"a": [1, 2, 3]})
