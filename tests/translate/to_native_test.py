from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

import narwhals.stable.v1 as nw


@pytest.mark.parametrize(
    ("method", "strict", "context"),
    [
        ("head", True, does_not_raise()),
        ("head", False, does_not_raise()),
        ("to_numpy", False, does_not_raise()),
        (
            "to_numpy",
            True,
            pytest.raises(TypeError, match="Expected Narwhals object, got"),
        ),
    ],
)
def test_to_native(
    constructor_eager: Any, method: str, strict: Any, context: Any
) -> None:
    df = nw.from_native(constructor_eager({"a": [1, 2, 3]}))

    with context:
        nw.to_native(getattr(df, method)(), strict=strict)

    s = df["a"]

    with context:
        nw.to_native(getattr(s, method)(), strict=strict)
