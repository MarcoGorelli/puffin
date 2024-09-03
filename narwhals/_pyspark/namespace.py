from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING

from narwhals import dtypes
from narwhals._expression_parsing import parse_into_exprs
from narwhals._pyspark.expr import PySparkExpr

if TYPE_CHECKING:
    from narwhals._pyspark.typing import IntoPySparkExpr


class PySparkNamespace:
    Int64 = dtypes.Int64
    Int32 = dtypes.Int32
    Int16 = dtypes.Int16
    Int8 = dtypes.Int8
    UInt64 = dtypes.UInt64
    UInt32 = dtypes.UInt32
    UInt16 = dtypes.UInt16
    UInt8 = dtypes.UInt8
    Float64 = dtypes.Float64
    Float32 = dtypes.Float32
    Boolean = dtypes.Boolean
    Object = dtypes.Object
    Unknown = dtypes.Unknown
    Categorical = dtypes.Categorical
    Enum = dtypes.Enum
    String = dtypes.String
    Datetime = dtypes.Datetime
    Duration = dtypes.Duration
    Date = dtypes.Date

    def __init__(self) -> None:
        pass

    def all_horizontal(self, *exprs: IntoPySparkExpr) -> PySparkExpr:
        return reduce(lambda x, y: x & y, parse_into_exprs(*exprs, namespace=self))

    def col(self, *column_names: str) -> PySparkExpr:
        return PySparkExpr.from_column_names(*column_names)