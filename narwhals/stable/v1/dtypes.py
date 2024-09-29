from narwhals.dtypes import Array
from narwhals.dtypes import Boolean
from narwhals.dtypes import Categorical
from narwhals.dtypes import Date
from narwhals.dtypes import Datetime as NwDatetime
from narwhals.dtypes import Duration
from narwhals.dtypes import Enum
from narwhals.dtypes import Float32
from narwhals.dtypes import Float64
from narwhals.dtypes import Int8
from narwhals.dtypes import Int16
from narwhals.dtypes import Int32
from narwhals.dtypes import Int64
from narwhals.dtypes import List
from narwhals.dtypes import Object
from narwhals.dtypes import String
from narwhals.dtypes import Struct
from narwhals.dtypes import UInt8
from narwhals.dtypes import UInt16
from narwhals.dtypes import UInt32
from narwhals.dtypes import UInt64
from narwhals.dtypes import Unknown


class Datetime(NwDatetime):
    """
    Data type representing a calendar date and time of day.

    Arguments:
        time_unit: Unit of time. Defaults to `'us'` (microseconds).
        time_zone: Time zone string, as defined in zoneinfo (to see valid strings run
            `import zoneinfo; zoneinfo.available_timezones()` for a full list).
            When used to match dtypes, can set this to "*" to check for Datetime
            columns that have any (non-null) timezone.

    Notes:
        Adapted from Polars implementation at:
        https://github.com/pola-rs/polars/blob/py-1.7.1/py-polars/polars/datatypes/classes.py#L398-L457
    """

    def __hash__(self) -> int:
        return hash(self.__class__)


__all__ = [
    "Array",
    "Boolean",
    "Categorical",
    "Date",
    "Datetime",
    "Duration",
    "Enum",
    "Float32",
    "Float64",
    "Int8",
    "Int16",
    "Int32",
    "Int64",
    "List",
    "Object",
    "String",
    "Struct",
    "UInt8",
    "UInt16",
    "UInt32",
    "UInt64",
    "Unknown",
]
