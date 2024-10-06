from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version


@pytest.mark.filterwarnings("ignore:.*Passing a BlockManager.*:DeprecationWarning")
@pytest.mark.skipif(
    parse_version(pd.__version__) < parse_version("2.0.0"),
    reason="too old for pandas-pyarrow",
)
def test_convert_pandas(constructor_eager: Any, request: pytest.FixtureRequest) -> None:
    if "modin" in str(constructor_eager):
        request.applymarker(pytest.mark.xfail)
    data = {"a": [1, 3, 2], "b": [4, 4, 6], "z": [7.0, 8, 9]}
    df_raw = constructor_eager(data)
    result = nw.from_native(df_raw).to_pandas()  # type: ignore[union-attr]

    if constructor_eager.__name__.startswith("pandas"):
        expected = constructor_eager(data)
    else:
        expected = pd.DataFrame(data)

    pd.testing.assert_frame_equal(result, expected)
