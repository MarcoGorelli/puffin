from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

import hypothesis.strategies as st
import numpy as np
import polars as pl
import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import settings
from hypothesis.extra.numpy import arrays

import narwhals as nw
from tests.conftest import pandas_constructor
from tests.conftest import pyarrow_table_constructor
from tests.utils import compare_dicts

if TYPE_CHECKING:
    from collections.abc import Sequence

    from narwhals.typing import IntoDataFrame


@pytest.fixture(
    params=[
        pandas_constructor,
        pyarrow_table_constructor,
    ],
    scope="module",
)
def constructor(request: pytest.FixtureRequest) -> Callable[[Any], IntoDataFrame]:
    return request.param  # type: ignore[no-any-return]


TEST_DATA = {
    "a": [1, 2, 3],
    "b": [4, 5, 6],
    "c": [7, 8, 9],
    "d": [1, 4, 2],
}
TEST_DATA_COLUMNS = list(TEST_DATA.keys())
TEST_DATA_NUM_ROWS = len(TEST_DATA[TEST_DATA_COLUMNS[0]])


@st.composite  # type: ignore[misc]
def string_slice(
    draw: st.DrawFn,
    strs: Sequence[str],
) -> slice:
    """
    Return slices such as `"a":`, `"a":"c"`, `"a":"c":2`, etc.
    """
    n_cols = len(strs)
    index_slice = draw(
        st.slices(n_cols).filter(
            lambda x: (
                (x.start is None or 0 <= x.start < n_cols)
                and (x.stop is None or 0 <= x.stop < n_cols)
            ),
        )
    )
    start = strs[index_slice.start] if index_slice.start is not None else None
    stop = strs[index_slice.stop] if index_slice.stop is not None else None

    return slice(start, stop, index_slice.step)


single_selector = st.one_of(
    # str selectors: columns:
    st.sampled_from(TEST_DATA_COLUMNS),
    string_slice(TEST_DATA_COLUMNS),
    st.lists(
        st.sampled_from(TEST_DATA_COLUMNS),
        unique=True,
    ),
    # int selectors: rows:
    st.slices(TEST_DATA_NUM_ROWS),
    st.lists(
        st.integers(
            min_value=0,  # pyarrow does not support negative indexing
            max_value=TEST_DATA_NUM_ROWS - 1,
        )
    ),
    st.integers(
        min_value=0,  # pyarrow does not support negative indexing
        max_value=TEST_DATA_NUM_ROWS - 1,
    ),
)


@st.composite  # type: ignore[misc]
def tuple_selector(draw: st.DrawFn) -> tuple[Any, Any]:
    rows = st.one_of(
        st.lists(
            st.integers(
                min_value=0,  # pyarrow does not support negative indexing
                max_value=TEST_DATA_NUM_ROWS - 1,
            ),
        ),
        st.integers(
            min_value=0,  # pyarrow does not support negative indexing
            max_value=TEST_DATA_NUM_ROWS - 1,
        ),
        st.slices(TEST_DATA_NUM_ROWS),
        arrays(
            dtype=st.sampled_from([np.int8, np.int16, np.int32, np.int64]),
            shape=st.integers(min_value=0, max_value=10),
            elements=st.integers(
                min_value=0,  # pyarrow does not support negative indexing
                max_value=TEST_DATA_NUM_ROWS - 1,
            ),
        ),
    )
    columns = st.one_of(
        st.lists(
            st.sampled_from(TEST_DATA_COLUMNS),
            unique=True,
        ),
        st.lists(
            st.integers(
                min_value=0,  # pyarrow does not support negative indexing
                max_value=TEST_DATA_NUM_ROWS - 1,
            ),
            unique=True,
        ),
        string_slice(TEST_DATA_COLUMNS),
        st.slices(len(TEST_DATA_COLUMNS)),
        st.sampled_from(TEST_DATA_COLUMNS),
        st.integers(min_value=0, max_value=len(TEST_DATA_COLUMNS) - 1),
    )

    return draw(rows), draw(columns)


@settings(max_examples=10000)  # type: ignore[misc]
@given(
    selector=st.one_of(
        single_selector,
        tuple_selector(),
    ),
)  # type: ignore[misc]
def test_getitem(
    constructor: Any,
    selector: Any,
) -> None:
    """
    Compare __getitem__ against polars.
    """

    # TODO(PR - clean up): documenting current differences
    if constructor is pyarrow_table_constructor:
        # NotImplementedError: Slicing with step is not supported on PyArrow tables
        assume(not isinstance(selector, slice) or selector.step in (None, 1))

        # IndexError: Offset must be non-negative (pyarrow does not support negative indexing)
        assume(
            not isinstance(selector, slice)
            or isinstance(selector.start, int)
            and selector.start >= 0
        )
        assume(
            not isinstance(selector, slice)
            or isinstance(selector.stop, int)
            and selector.stop >= 0
        )

        # Pairs of slices are not supported
        # NB a few trivial cases are supported, eg df[0:1, :]
        # TypeError: Got unexpected argument type <class 'slice'> for compute function
        assume(
            not (
                isinstance(selector, tuple)
                and isinstance(selector[0], slice)
                and isinstance(selector[1], slice)
                and (
                    selector[0] != slice(None, None, None)
                    or selector[1] != slice(None, None, None)
                )
            )
        )

        # df[[], "a":], df[[], :] etc fail in pyarrow:
        # ArrowNotImplementedError: Function 'array_take' has no kernel matching input types (int64, null)
        assume(
            not (
                isinstance(selector, tuple)
                and isinstance(selector[0], list)
                and len(selector[0]) == 0
                and isinstance(selector[1], slice)
            )
        )

    elif constructor is pandas_constructor:
        # df[[], "a":], df[[], :] etc return different results between pandas/polars:
        assume(
            not (
                isinstance(selector, tuple)
                and isinstance(selector[0], list)
                and len(selector[0]) == 0
                and isinstance(selector[1], slice)
            )
        )

    # df[..., ::step] is not fine:
    # TypeError: Expected slice of integers or strings, got: <class 'slice'>
    assume(
        not (
            isinstance(selector, tuple)
            and isinstance(selector[1], slice)
            and selector[1].start is None
            and selector[1].stop is None
        )
    )
    # End TODO ================================================================

    df_polars = nw.from_native(pl.DataFrame(TEST_DATA))
    try:
        result_polars = df_polars[selector]
    except TypeError:
        # If the selector fails on polars, then skip the test.
        # e.g. df[0, 'a'] fails, suggesting to use DataFrame.item to extract a single
        # element.
        # This allows us to test single-element selection on just one of the
        # rows/columns sides.
        return

    df_other = nw.from_native(constructor(TEST_DATA))
    result_other = df_other[selector]

    if hasattr(result_polars, "to_dict"):
        compare_dicts(
            result_polars.to_dict(),
            result_other.to_dict(),  # type: ignore[union-attr]
        )
    else:
        assert result_polars.to_list() == result_other.to_list()  # type: ignore[union-attr]
