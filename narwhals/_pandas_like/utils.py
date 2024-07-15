from __future__ import annotations

import secrets
from enum import Enum
from enum import auto
from functools import wraps
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Iterable
from typing import TypeVar

from narwhals.dependencies import get_cudf
from narwhals.dependencies import get_dask
from narwhals.dependencies import get_modin
from narwhals.dependencies import get_numpy
from narwhals.dependencies import get_pandas
from narwhals.dependencies import get_pyarrow
from narwhals.utils import isinstance_or_issubclass

T = TypeVar("T")

if TYPE_CHECKING:
    from narwhals._arrow.typing import IntoArrowExpr
    from narwhals._pandas_like.dataframe import PandasLikeDataFrame
    from narwhals._pandas_like.expr import PandasLikeExpr
    from narwhals._pandas_like.series import PandasLikeSeries
    from narwhals._pandas_like.typing import IntoPandasLikeExpr
    from narwhals.dtypes import DType

    ExprT = TypeVar("ExprT", bound=PandasLikeExpr)


class Implementation(Enum):
    PANDAS = auto()
    MODIN = auto()
    CUDF = auto()
    DASK = auto()


def validate_column_comparand(index: Any, other: Any) -> Any:
    """Validate RHS of binary operation.

    If the comparison isn't supported, return `NotImplemented` so that the
    "right-hand-side" operation (e.g. `__radd__`) can be tried.

    If RHS is length 1, return the scalar value, so that the underlying
    library can broadcast it.
    """
    from narwhals._pandas_like.dataframe import PandasLikeDataFrame
    from narwhals._pandas_like.series import PandasLikeSeries

    if isinstance(other, list):
        if len(other) > 1:
            # e.g. `plx.all() + plx.all()`
            msg = "Multi-output expressions are not supported in this context"
            raise ValueError(msg)
        other = other[0]
    if isinstance(other, PandasLikeDataFrame):
        return NotImplemented
    if isinstance(other, PandasLikeSeries):
        if other.len() == 1:
            # broadcast
            return other.item()
        if (
            other._native_series.index is not index
            and other._implementation != Implementation.DASK
        ):
            return set_axis(
                other._native_series,
                index,
                implementation=other._implementation,
                backend_version=other._backend_version,
            )
        return other._native_series
    return other


def validate_dataframe_comparand(index: Any, other: Any) -> Any:
    """Validate RHS of binary operation.

    If the comparison isn't supported, return `NotImplemented` so that the
    "right-hand-side" operation (e.g. `__radd__`) can be tried.
    """
    from narwhals._pandas_like.dataframe import PandasLikeDataFrame
    from narwhals._pandas_like.series import PandasLikeSeries

    if isinstance(other, PandasLikeDataFrame):
        return NotImplemented
    if isinstance(other, PandasLikeSeries):
        if other.len() == 1:
            # broadcast
            return other._native_series.iloc[0]
        if (
            other._native_series.index is not index
            and other._implementation is not Implementation.DASK
        ):
            return set_axis(
                other._native_series,
                index,
                implementation=other._implementation,
                backend_version=other._backend_version,
            )
        return other._native_series
        return other._series
    raise AssertionError("Please report a bug")


def maybe_evaluate_expr(df: PandasLikeDataFrame, expr: Any) -> Any:
    """Evaluate `expr` if it's an expression, otherwise return it as is."""

    if isinstance(expr, PandasLikeExpr):
        return expr._call(df)
    return expr


def parse_into_expr(
    implementation: str, into_expr: IntoPandasLikeExpr | IntoArrowExpr
) -> PandasLikeExpr:
    """Parse `into_expr` as an expression.

    For example, in Polars, we can do both `df.select('a')` and `df.select(pl.col('a'))`.
    We do the same in Narwhals:

    - if `into_expr` is already an expression, just return it
    - if it's a Series, then convert it to an expression
    - if it's a numpy array, then convert it to a Series and then to an expression
    - if it's a string, then convert it to an expression
    - else, raise
    """
    from narwhals._arrow.expr import ArrowExpr
    from narwhals._arrow.namespace import ArrowNamespace
    from narwhals._arrow.series import ArrowSeries
    from narwhals._pandas_like.expr import PandasLikeExpr
    from narwhals._pandas_like.namespace import PandasLikeNamespace
    from narwhals._pandas_like.series import PandasLikeSeries

    if implementation == "arrow":
        plx: ArrowNamespace | PandasLikeNamespace = ArrowNamespace()
    else:
        PandasLikeNamespace(implementation=implementation)
    if isinstance(into_expr, (PandasLikeExpr, ArrowExpr)):
        return into_expr  # type: ignore[return-value]
    if isinstance(into_expr, (PandasLikeSeries, ArrowSeries)):
        return plx._create_expr_from_series(into_expr)  # type: ignore[arg-type, return-value]
    if isinstance(into_expr, str):
        return plx.col(into_expr)  # type: ignore[return-value]
    if (np := get_numpy()) is not None and isinstance(into_expr, np.ndarray):
        series = create_native_series(into_expr, implementation=implementation)
        return plx._create_expr_from_series(series)  # type: ignore[arg-type, return-value]
    msg = f"Expected IntoExpr, got {type(into_expr)}"  # pragma: no cover
    raise AssertionError(msg)


def create_native_series(
    iterable: Any,
    index: Any = None,
    *,
    implementation: Implementation,
    backend_version: tuple[int, ...],
) -> PandasLikeSeries:
    from narwhals._pandas_like.series import PandasLikeSeries

    if implementation is Implementation.PANDAS:
        pd = get_pandas()
        series = pd.Series(iterable, index=index, name="")
    elif implementation is Implementation.MODIN:
        mpd = get_modin()
        series = mpd.Series(iterable, index=index, name="")
    elif implementation is Implementation.CUDF:
        cudf = get_cudf()
        series = cudf.Series(iterable, index=index, name="")
    return PandasLikeSeries(
        series, implementation=implementation, backend_version=backend_version
    )


def horizontal_concat(
    dfs: list[Any], *, implementation: Implementation, backend_version: tuple[int, ...]
) -> Any:
    """
    Concatenate (native) DataFrames horizontally.

    Should be in namespace.
    """
    if implementation is Implementation.PANDAS:
        pd = get_pandas()

        if backend_version < (3,):
            return pd.concat(dfs, axis=1, copy=False)
        return pd.concat(dfs, axis=1)  # pragma: no cover
    if implementation is Implementation.CUDF:  # pragma: no cover
        cudf = get_cudf()

        return cudf.concat(dfs, axis=1)
    if implementation is Implementation.MODIN:  # pragma: no cover
        mpd = get_modin()

        return mpd.concat(dfs, axis=1)
    if implementation is Implementation.DASK:  # pragma: no cover
        dd = get_dask()
        if hasattr(dfs[0], "_series"):
            return dd.concat([i._series for i in dfs], axis=1)
        return dd.concat(dfs, axis=1)
    msg = f"Unknown implementation: {implementation}"  # pragma: no cover
    raise TypeError(msg)  # pragma: no cover


def vertical_concat(
    dfs: list[Any], *, implementation: Implementation, backend_version: tuple[int, ...]
) -> Any:
    """
    Concatenate (native) DataFrames vertically.

    Should be in namespace.
    """
    if not dfs:
        msg = "No dataframes to concatenate"  # pragma: no cover
        raise AssertionError(msg)
    cols = set(dfs[0].columns)
    for df in dfs:
        cols_current = set(df.columns)
        if cols_current != cols:
            msg = "unable to vstack, column names don't match"
            raise TypeError(msg)
    if implementation is Implementation.PANDAS:
        pd = get_pandas()

        if backend_version < (3,):
            return pd.concat(dfs, axis=0, copy=False)
        return pd.concat(dfs, axis=0)  # pragma: no cover
    if implementation is Implementation.CUDF:  # pragma: no cover
        cudf = get_cudf()

        return cudf.concat(dfs, axis=0)
    if implementation is Implementation.MODIN:  # pragma: no cover
        mpd = get_modin()

        return mpd.concat(dfs, axis=0)
    if implementation is Implementation.DASK:  # pragma: no cover
        dd = get_dask()

        return dd.concat(dfs, axis=0)
    msg = f"Unknown implementation: {implementation}"  # pragma: no cover
    raise TypeError(msg)  # pragma: no cover


def native_series_from_iterable(
    data: Iterable[Any],
    name: str,
    index: Any,
    implementation: Implementation,
) -> Any:
    """Return native series."""
    if implementation is Implementation.PANDAS:
        pd = get_pandas()

        return pd.Series(data, name=name, index=index, copy=False)
    if implementation is Implementation.CUDF:  # pragma: no cover
        cudf = get_cudf()

        return cudf.Series(data, name=name, index=index)
    if implementation is Implementation.MODIN:  # pragma: no cover
        mpd = get_modin()

        return mpd.Series(data, name=name, index=index)
    if implementation == "arrow":
        pa = get_pyarrow()
        return pa.chunked_array([data])
    if implementation is Implementation.DASK:  # pragma: no cover
        dd = get_dask()
        pd = get_pandas()
        if hasattr(data[0], "compute"):  # type: ignore
            return dd.concat([i.to_series() for i in data])
        return pd.Series(
            data,
            name=name,
            index=index,
            copy=False,
        ).pipe(dd.from_pandas)
    msg = f"Unknown implementation: {implementation}"  # pragma: no cover
    raise TypeError(msg)  # pragma: no cover


def set_axis(
    obj: T,
    index: Any,
    *,
    implementation: Implementation,
    backend_version: tuple[int, ...],
) -> T:
    if implementation is Implementation.PANDAS and backend_version < (
        1,
    ):  # pragma: no cover
        kwargs = {"inplace": False}
    else:
        kwargs = {}
    if implementation is Implementation.PANDAS and backend_version >= (
        1,
        5,
    ):  # pragma: no cover
        kwargs["copy"] = False
    else:  # pragma: no cover
        pass
    if implementation is Implementation.DASK:
        msg = "Setting axis on columns is not currently supported for dask"
        raise NotImplementedError(msg)
    return obj.set_axis(index, axis=0, **kwargs)  # type: ignore[no-any-return, attr-defined]


def translate_dtype(column: Any) -> DType:
    from narwhals import dtypes

    dtype = column.dtype
    if str(dtype) in ("int64", "Int64", "Int64[pyarrow]", "int64[pyarrow]"):
        return dtypes.Int64()
    if str(dtype) in ("int32", "Int32", "Int32[pyarrow]", "int32[pyarrow]"):
        return dtypes.Int32()
    if str(dtype) in ("int16", "Int16", "Int16[pyarrow]", "int16[pyarrow]"):
        return dtypes.Int16()
    if str(dtype) in ("int8", "Int8", "Int8[pyarrow]", "int8[pyarrow]"):
        return dtypes.Int8()
    if str(dtype) in ("uint64", "UInt64", "UInt64[pyarrow]", "uint64[pyarrow]"):
        return dtypes.UInt64()
    if str(dtype) in ("uint32", "UInt32", "UInt32[pyarrow]", "uint32[pyarrow]"):
        return dtypes.UInt32()
    if str(dtype) in ("uint16", "UInt16", "UInt16[pyarrow]", "uint16[pyarrow]"):
        return dtypes.UInt16()
    if str(dtype) in ("uint8", "UInt8", "UInt8[pyarrow]", "uint8[pyarrow]"):
        return dtypes.UInt8()
    if str(dtype) in (
        "float64",
        "Float64",
        "Float64[pyarrow]",
        "float64[pyarrow]",
        "double[pyarrow]",
    ):
        return dtypes.Float64()
    if str(dtype) in (
        "float32",
        "Float32",
        "Float32[pyarrow]",
        "float32[pyarrow]",
        "float[pyarrow]",
    ):
        return dtypes.Float32()
    if str(dtype) in (
        "string",
        "string[python]",
        "string[pyarrow]",
        "large_string[pyarrow]",
    ):
        return dtypes.String()
    if str(dtype) in ("bool", "boolean", "boolean[pyarrow]", "bool[pyarrow]"):
        return dtypes.Boolean()
    if str(dtype) in ("category",) or str(dtype).startswith("dictionary<"):
        return dtypes.Categorical()
    if str(dtype).startswith("datetime64"):
        # TODO(Unassigned): different time units and time zones
        return dtypes.Datetime()
    if str(dtype).startswith("timedelta64") or str(dtype).startswith("duration"):
        # TODO(Unassigned): different time units
        return dtypes.Duration()
    if str(dtype).startswith("timestamp["):
        # pyarrow-backed datetime
        # TODO(Unassigned): different time units and time zones
        return dtypes.Datetime()
    if str(dtype) == "date32[day][pyarrow]":
        return dtypes.Date()
    if str(dtype) == "object":
        if (idx := column.first_valid_index()) is not None and isinstance(
            column.loc[idx], str
        ):
            # Infer based on first non-missing value.
            # For pandas pre 3.0, this isn't perfect.
            # After pandas 3.0, pandas has a dedicated string dtype
            # which is inferred by default.
            return dtypes.String()
        return dtypes.Object()
    return dtypes.Unknown()


def get_dtype_backend(dtype: Any, implementation: Implementation) -> str:
    if implementation is Implementation.PANDAS:
        pd = get_pandas()
        if hasattr(pd, "ArrowDtype") and isinstance(dtype, pd.ArrowDtype):
            return "pyarrow-nullable"

        try:
            if isinstance(dtype, pd.core.dtypes.dtypes.BaseMaskedDtype):
                return "pandas-nullable"
        except AttributeError:  # pragma: no cover
            # defensive check for old pandas versions
            pass
        return "numpy"
    else:  # pragma: no cover
        return "numpy"


def reverse_translate_dtype(  # noqa: PLR0915
    dtype: DType | type[DType], starting_dtype: Any, implementation: Implementation
) -> Any:
    from narwhals import dtypes

    dtype_backend = get_dtype_backend(starting_dtype, implementation)
    if isinstance_or_issubclass(dtype, dtypes.Float64):
        if dtype_backend == "pyarrow-nullable":
            return "Float64[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "Float64"
        else:
            return "float64"
    if isinstance_or_issubclass(dtype, dtypes.Float32):
        if dtype_backend == "pyarrow-nullable":
            return "Float32[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "Float32"
        else:
            return "float32"
    if isinstance_or_issubclass(dtype, dtypes.Int64):
        if dtype_backend == "pyarrow-nullable":
            return "Int64[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "Int64"
        else:
            return "int64"
    if isinstance_or_issubclass(dtype, dtypes.Int32):
        if dtype_backend == "pyarrow-nullable":
            return "Int32[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "Int32"
        else:
            return "int32"
    if isinstance_or_issubclass(dtype, dtypes.Int16):
        if dtype_backend == "pyarrow-nullable":
            return "Int16[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "Int16"
        else:
            return "int16"
    if isinstance_or_issubclass(dtype, dtypes.Int8):
        if dtype_backend == "pyarrow-nullable":
            return "Int8[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "Int8"
        else:
            return "int8"
    if isinstance_or_issubclass(dtype, dtypes.UInt64):
        if dtype_backend == "pyarrow-nullable":
            return "UInt64[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "UInt64"
        else:
            return "uint64"
    if isinstance_or_issubclass(dtype, dtypes.UInt32):
        if dtype_backend == "pyarrow-nullable":
            return "UInt32[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "UInt32"
        else:
            return "uint32"
    if isinstance_or_issubclass(dtype, dtypes.UInt16):
        if dtype_backend == "pyarrow-nullable":
            return "UInt16[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "UInt16"
        else:
            return "uint16"
    if isinstance_or_issubclass(dtype, dtypes.UInt8):
        if dtype_backend == "pyarrow-nullable":
            return "UInt8[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "UInt8"
        else:
            return "uint8"
    if isinstance_or_issubclass(dtype, dtypes.String):
        if dtype_backend == "pyarrow-nullable":
            return "string[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "string"
        else:
            return str
    if isinstance_or_issubclass(dtype, dtypes.Boolean):
        if dtype_backend == "pyarrow-nullable":
            return "boolean[pyarrow]"
        if dtype_backend == "pandas-nullable":
            return "boolean"
        else:
            return "bool"
    if isinstance_or_issubclass(dtype, dtypes.Categorical):
        # TODO(Unassigned): is there no pyarrow-backed categorical?
        # or at least, convert_dtypes(dtype_backend='pyarrow') doesn't
        # convert to it?
        return "category"
    if isinstance_or_issubclass(dtype, dtypes.Datetime):
        # TODO(Unassigned): different time units and time zones
        if dtype_backend == "pyarrow-nullable":
            return "timestamp[ns][pyarrow]"
        return "datetime64[ns]"
    if isinstance_or_issubclass(dtype, dtypes.Duration):
        # TODO(Unassigned): different time units and time zones
        if dtype_backend == "pyarrow-nullable":
            return "duration[ns][pyarrow]"
        return "timedelta64[ns]"
    if isinstance_or_issubclass(dtype, dtypes.Date):
        if dtype_backend == "pyarrow-nullable":
            return "date32[pyarrow]"
        msg = "Date dtype only supported for pyarrow-backed data types in pandas"
        raise NotImplementedError(msg)
    msg = f"Unknown dtype: {dtype}"  # pragma: no cover
    raise AssertionError(msg)


def validate_indices(series: list[PandasLikeSeries]) -> list[Any]:
    idx = series[0]._native_series.index
    reindexed = [series[0]._native_series]
    for s in series[1:]:
        if s._native_series.index is not idx:
            reindexed.append(
                set_axis(
                    s._native_series,
                    idx,
                    implementation=s._implementation,
                    backend_version=s._backend_version,
                )
            )
        else:
            reindexed.append(s._native_series)
    return reindexed


def to_datetime(implementation: Implementation) -> Any:
    if implementation is Implementation.PANDAS:
        return get_pandas().to_datetime
    if implementation is Implementation.MODIN:
        return get_modin().to_datetime
    if implementation is Implementation.CUDF:
        return get_cudf().to_datetime
    if implementation is Implementation.DASK:
        return get_dask().to_datetime
    raise AssertionError


def int_dtype_mapper(dtype: Any) -> str:
    if "pyarrow" in str(dtype):
        return "Int64[pyarrow]"
    if str(dtype).lower() != str(dtype):  # pragma: no cover
        return "Int64"
    return "int64"


def generate_unique_token(n_bytes: int, columns: list[str]) -> str:  # pragma: no cover
    """Generates a unique token of specified n_bytes that is not present in the given list of columns.

    Arguments:
        n_bytes : The number of bytes to generate for the token.
        columns : The list of columns to check for uniqueness.

    Returns:
        A unique token that is not present in the given list of columns.

    Raises:
        AssertionError: If a unique token cannot be generated after 100 attempts.
    """
    counter = 0
    while True:
        token = secrets.token_hex(n_bytes)
        if token not in columns:
            return token

        counter += 1
        if counter > 100:
            msg = (
                "Internal Error: Narwhals was not able to generate a column name to perform cross "
                "join operation"
            )
            raise AssertionError(msg)


def not_implemented_in(
    *implementations: Implementation,
) -> Callable[[Callable], Callable]:  # type: ignore
    """
    Produces method decorator to raise not implemented warnings for given implementations
    """

    def check_implementation_wrapper(func: Callable) -> Callable:  # type: ignore
        """Wraps function to return same function + implementation check"""

        @wraps(func)  # type: ignore
        def wrapped_func(self, *args, **kwargs):
            """Checks implementation then carries out wrapped call"""
            if (implementation := self._implementation) in implementations:
                raise NotImplementedError(f"Not implemented in {implementation}")
            return func(self, *args, **kwargs)

        return wrapped_func

    return check_implementation_wrapper
