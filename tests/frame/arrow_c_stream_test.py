import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pytest

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version


@pytest.mark.skipif(
    parse_version(pl.__version__) < (1, 3), reason="too old for pycapsule in Polars"
)
def test_arrow_c_stream_test() -> None:
    df = nw.from_native(pl.Series([1, 2, 3]).to_frame("a"), eager_only=True)
    result = pa.table(df)
    expected = pa.table({"a": [1, 2, 3]})
    assert pc.all(pc.equal(result["a"], expected["a"])).as_py()


@pytest.mark.skipif(
    parse_version(pl.__version__) < (1, 3), reason="too old for pycapsule in Polars"
)
def test_arrow_c_stream_test_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    # "poison" the dunder method to make sure it actually got called above
    monkeypatch.setattr(
        "narwhals.dataframe.DataFrame.__arrow_c_stream__", lambda *_: 1 / 0
    )
    df = nw.from_native(pl.Series([1, 2, 3]).to_frame("a"), eager_only=True)
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        pa.table(df)


@pytest.mark.skipif(
    parse_version(pl.__version__) < (1, 3), reason="too old for pycapsule in Polars"
)
def test_arrow_c_stream_test_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    # Check that fallback to PyArrow works
    monkeypatch.delattr("polars.DataFrame.__arrow_c_stream__")
    df = nw.from_native(pl.Series([1, 2, 3]).to_frame("a"), eager_only=True)
    result = pa.table(df)
    expected = pa.table({"a": [1, 2, 3]})
    assert pc.all(pc.equal(result["a"], expected["a"])).as_py()
