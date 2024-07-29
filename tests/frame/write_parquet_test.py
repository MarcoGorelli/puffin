from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version

data = {"a": [1, 2, 3]}


@pytest.mark.skipif(
    parse_version(pd.__version__) < parse_version("2.0.0"), reason="too old for pyarrow"
)
def test_write_parquet(constructor_eager: Any, tmpdir: pytest.TempdirFactory) -> None:
    path = tmpdir / "foo.parquet"  # type: ignore[operator]
    nw.from_native(constructor_eager(data), eager_only=True).write_parquet(str(path))
    assert path.exists()
