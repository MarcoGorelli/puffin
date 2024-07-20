from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from narwhals._polars.namespace import PolarsNamespace
from narwhals._polars.utils import extract_args_kwargs
from narwhals._polars.utils import translate_dtype
from narwhals.dependencies import get_polars

if TYPE_CHECKING:
    from typing_extensions import Self


class PolarsDataFrame:
    def __init__(self, df: Any) -> None:
        self._native_dataframe = df

    def __repr__(self) -> str:
        return "PolarsDataFrame"

    def __narwhals_dataframe__(self) -> Self:
        return self

    def __narwhals_namespace__(self) -> PolarsNamespace:
        return PolarsNamespace()

    def __native_namespace__(self) -> Any:
        return get_polars()

    def _from_native_object(self, obj: Any) -> Any:
        pl = get_polars()
        if isinstance(obj, pl.Series):
            from narwhals._polars.series import PolarsSeries

            return PolarsSeries(obj)
        if isinstance(obj, pl.DataFrame):
            return self.__class__(obj)
        if isinstance(obj, pl.LazyFrame):
            from narwhals._polars.dataframe import PolarsLazyFrame

            return PolarsLazyFrame(obj)
        # scalar
        return obj

    def __getattr__(self, attr: str) -> Any:
        def func(*args: Any, **kwargs: Any) -> Any:
            args, kwargs = extract_args_kwargs(args, kwargs)  # type: ignore[assignment]
            return self._from_native_object(
                getattr(self._native_dataframe, attr)(*args, **kwargs)
            )

        return func

    @property
    def schema(self) -> dict[str, Any]:
        schema = self._native_dataframe.schema
        return {name: translate_dtype(dtype) for name, dtype in schema.items()}

    def collect_schema(self) -> dict[str, Any]:
        schema = dict(self._native_dataframe.collect_schema())
        return {name: translate_dtype(dtype) for name, dtype in schema.items()}

    @property
    def shape(self) -> tuple[int, int]:
        return self._native_dataframe.shape  # type: ignore[no-any-return]

    def __getitem__(self, item: Any) -> Any:
        pl = get_polars()
        result = self._native_dataframe.__getitem__(item)
        if isinstance(result, pl.Series):
            from narwhals._polars.series import PolarsSeries

            return PolarsSeries(result)
        return self._from_native_object(result)

    def get_column(self, name: str) -> Any:
        from narwhals._polars.series import PolarsSeries

        return PolarsSeries(self._native_dataframe.get_column(name))

    def is_empty(self) -> bool:
        return len(self._native_dataframe) == 0

    @property
    def columns(self) -> list[str]:
        return self._native_dataframe.columns  # type: ignore[no-any-return]

    def lazy(self) -> PolarsLazyFrame:
        return PolarsLazyFrame(self._native_dataframe.lazy())

    def to_dict(self, *, as_series: bool) -> Any:
        df = self._native_dataframe

        if as_series:
            from narwhals._polars.series import PolarsSeries

            return {
                name: PolarsSeries(col)
                for name, col in df.to_dict(as_series=True).items()
            }
        else:
            return df.to_dict(as_series=False)


class PolarsLazyFrame:
    def __init__(self, df: Any) -> None:
        self._native_dataframe = df

    def __repr__(self) -> str:
        return "PolarsLazyFrame"

    def __narwhals_lazyframe__(self) -> Self:
        return self

    def __narwhals_namespace__(self) -> PolarsNamespace:
        return PolarsNamespace()

    def _from_native_object(self, df: Any) -> Self:
        return self.__class__(df)

    def __getattr__(self, attr: str) -> Any:
        def func(*args: Any, **kwargs: Any) -> Any:
            args, kwargs = extract_args_kwargs(args, kwargs)  # type: ignore[assignment]
            return self._from_native_object(
                getattr(self._native_dataframe, attr)(*args, **kwargs)
            )

        return func

    @property
    def columns(self) -> list[str]:
        return self._native_dataframe.columns  # type: ignore[no-any-return]

    @property
    def schema(self) -> dict[str, Any]:
        schema = self._native_dataframe.schema
        return {name: translate_dtype(dtype) for name, dtype in schema.items()}

    def collect_schema(self) -> dict[str, Any]:
        schema = dict(self._native_dataframe.collect_schema())
        return {name: translate_dtype(dtype) for name, dtype in schema.items()}

    def collect(self) -> PolarsDataFrame:
        return PolarsDataFrame(self._native_dataframe.collect())
