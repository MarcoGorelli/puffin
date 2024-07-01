from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl
import pytest

import narwhals as nw

data = {"a": [1, 2, 3]}


@pytest.mark.parametrize("constructor", [pd.DataFrame, pl.DataFrame])
def test_write_parquet(constructor: Any, tmpdir: pytest.TempdirFactory) -> None:
    path = Path(str(tmpdir)) / "foo.parquet"
    nw.from_native(constructor(data), eager_only=True).write_parquet(path)
    assert path.exists()
