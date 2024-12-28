from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Any

from narwhals.exceptions import InvalidIntoExprError
from narwhals.utils import import_dtypes_module

if TYPE_CHECKING:
    import duckdb

    from narwhals._duckdb.dataframe import DuckDBInterchangeFrame
    from narwhals._duckdb.typing import IntoDuckDBExpr
    from narwhals.dtypes import DType
    from narwhals.utils import Version


def get_column_name(df: DuckDBInterchangeFrame, column: duckdb.Expression) -> str:
    return str(df._native_frame.select(column).columns[0])


def maybe_evaluate(df: DuckDBInterchangeFrame, obj: Any) -> Any:
    import duckdb

    from narwhals._duckdb.expr import DuckDBExpr

    if isinstance(obj, DuckDBExpr):
        column_results = obj._call(df)
        if len(column_results) != 1:  # pragma: no cover
            msg = "Multi-output expressions (e.g. `nw.all()` or `nw.col('a', 'b')`) not supported in this context"
            raise NotImplementedError(msg)
        column_result = column_results[0]
        if obj._returns_scalar:
            msg = "Reductions are not yet supported for DuckDB, at least until they implement duckdb.WindowExpression"
            raise NotImplementedError(msg)
        return column_result
    return duckdb.ConstantExpression(obj)


def parse_exprs_and_named_exprs(
    df: DuckDBInterchangeFrame,
    *exprs: IntoDuckDBExpr,
    **named_exprs: IntoDuckDBExpr,
) -> dict[str, duckdb.Expression]:
    result_columns: dict[str, list[duckdb.Expression]] = {}
    for expr in exprs:
        column_list = _columns_from_expr(df, expr)
        if isinstance(expr, str):  # pragma: no cover
            output_names = [expr]
        elif expr._output_names is None:
            output_names = [get_column_name(df, col) for col in column_list]
        else:
            output_names = expr._output_names
        result_columns.update(zip(output_names, column_list))
    for col_alias, expr in named_exprs.items():
        columns_list = _columns_from_expr(df, expr)
        if len(columns_list) != 1:  # pragma: no cover
            msg = "Named expressions must return a single column"
            raise AssertionError(msg)
        result_columns[col_alias] = columns_list[0]
    return result_columns


def _columns_from_expr(
    df: DuckDBInterchangeFrame, expr: IntoDuckDBExpr
) -> list[duckdb.Expression]:
    if isinstance(expr, str):  # pragma: no cover
        from duckdb import ColumnExpression

        return [ColumnExpression(expr)]
    elif hasattr(expr, "__narwhals_expr__"):
        col_output_list = expr._call(df)
        if expr._output_names is not None and (
            len(col_output_list) != len(expr._output_names)
        ):  # pragma: no cover
            msg = "Safety assertion failed, please report a bug to https://github.com/narwhals-dev/narwhals/issues"
            raise AssertionError(msg)
        return col_output_list
    else:
        raise InvalidIntoExprError.from_invalid_type(type(expr))


@lru_cache(maxsize=16)
def native_to_narwhals_dtype(duckdb_dtype: str, version: Version) -> DType:
    dtypes = import_dtypes_module(version)
    if duckdb_dtype == "HUGEINT":
        return dtypes.Int128()
    if duckdb_dtype == "BIGINT":
        return dtypes.Int64()
    if duckdb_dtype == "INTEGER":
        return dtypes.Int32()
    if duckdb_dtype == "SMALLINT":
        return dtypes.Int16()
    if duckdb_dtype == "TINYINT":
        return dtypes.Int8()
    if duckdb_dtype == "UHUGEINT":
        return dtypes.UInt128()
    if duckdb_dtype == "UBIGINT":
        return dtypes.UInt64()
    if duckdb_dtype == "UINTEGER":
        return dtypes.UInt32()
    if duckdb_dtype == "USMALLINT":
        return dtypes.UInt16()
    if duckdb_dtype == "UTINYINT":
        return dtypes.UInt8()
    if duckdb_dtype == "DOUBLE":
        return dtypes.Float64()
    if duckdb_dtype == "FLOAT":
        return dtypes.Float32()
    if duckdb_dtype == "VARCHAR":
        return dtypes.String()
    if duckdb_dtype == "DATE":
        return dtypes.Date()
    if duckdb_dtype == "TIMESTAMP":
        return dtypes.Datetime()
    if duckdb_dtype == "BOOLEAN":
        return dtypes.Boolean()
    if duckdb_dtype == "INTERVAL":
        return dtypes.Duration()
    if duckdb_dtype.startswith("STRUCT"):
        matchstruc_ = re.findall(r"(\w+)\s+(\w+)", duckdb_dtype)
        return dtypes.Struct(
            [
                dtypes.Field(
                    matchstruc_[i][0],
                    native_to_narwhals_dtype(matchstruc_[i][1], version),
                )
                for i in range(len(matchstruc_))
            ]
        )
    if match_ := re.match(r"(.*)\[\]$", duckdb_dtype):
        return dtypes.List(native_to_narwhals_dtype(match_.group(1), version))
    if match_ := re.match(r"(\w+)\[(\d+)\]", duckdb_dtype):
        return dtypes.Array(
            native_to_narwhals_dtype(match_.group(1), version),
            int(match_.group(2)),
        )
    if duckdb_dtype.startswith("DECIMAL("):
        return dtypes.Decimal()
    return dtypes.Unknown()  # pragma: no cover
