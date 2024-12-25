from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Sequence

from narwhals._duckdb.utils import get_column_name
from narwhals._duckdb.utils import maybe_evaluate
from narwhals.typing import CompliantExpr
from narwhals.utils import Implementation

if TYPE_CHECKING:
    import duckdb
    from typing_extensions import Self

    from narwhals._duckdb.dataframe import DuckDBInterchangeFrame
    from narwhals._duckdb.namespace import DuckDBNamespace
    from narwhals.utils import Version


class DuckDBExpr(CompliantExpr["duckdb.Expression"]):
    _implementation = Implementation.DUCKDB

    def __init__(
        self,
        call: Callable[[DuckDBInterchangeFrame], list[duckdb.Expression]],
        *,
        depth: int,
        function_name: str,
        root_names: list[str] | None,
        output_names: list[str] | None,
        # Whether the expression is a length-1 Column resulting from
        # a reduction, such as `nw.col('a').sum()`
        returns_scalar: bool,
        backend_version: tuple[int, ...],
        version: Version,
        kwargs: dict[str, Any],
    ) -> None:
        self._call = call
        self._depth = depth
        self._function_name = function_name
        self._root_names = root_names
        self._output_names = output_names
        self._returns_scalar = returns_scalar
        self._backend_version = backend_version
        self._version = version
        self._kwargs = kwargs

    def __call__(self, df: DuckDBInterchangeFrame) -> Sequence[duckdb.Expression]:
        return self._call(df)

    def __narwhals_expr__(self) -> None: ...

    def __narwhals_namespace__(self) -> DuckDBNamespace:  # pragma: no cover
        # Unused, just for compatibility with PandasLikeExpr
        from narwhals._duckdb.namespace import DuckDBNamespace

        return DuckDBNamespace(
            backend_version=self._backend_version, version=self._version
        )

    @classmethod
    def from_column_names(
        cls: type[Self],
        *column_names: str,
        backend_version: tuple[int, ...],
        version: Version,
    ) -> Self:
        def func(_: DuckDBInterchangeFrame) -> list[duckdb.Expression]:
            from duckdb import ColumnExpression

            return [ColumnExpression(col_name) for col_name in column_names]

        return cls(
            func,
            depth=0,
            function_name="col",
            root_names=list(column_names),
            output_names=list(column_names),
            returns_scalar=False,
            backend_version=backend_version,
            version=version,
            kwargs={},
        )

    def _from_call(
        self,
        call: Callable[..., duckdb.Expression],
        expr_name: str,
        *,
        returns_scalar: bool,
        **kwargs: Any,
    ) -> Self:
        def func(df: DuckDBInterchangeFrame) -> list[duckdb.Expression]:
            results = []
            inputs = self._call(df)
            _kwargs = {key: maybe_evaluate(df, value) for key, value in kwargs.items()}
            for _input in inputs:
                input_col_name = get_column_name(df, _input)

                column_result = call(_input, **_kwargs)
                if not returns_scalar:
                    column_result = column_result.alias(input_col_name)
                results.append(column_result)
            return results

        # Try tracking root and output names by combining them from all
        # expressions appearing in args and kwargs. If any anonymous
        # expression appears (e.g. nw.all()), then give up on tracking root names
        # and just set it to None.
        root_names = copy(self._root_names)
        output_names = self._output_names
        for arg in list(kwargs.values()):
            if root_names is not None and isinstance(arg, self.__class__):
                if arg._root_names is not None:
                    root_names.extend(arg._root_names)
                else:  # pragma: no cover
                    root_names = None
                    output_names = None
                    break
            elif root_names is None:
                output_names = None
                break

        if not (
            (output_names is None and root_names is None)
            or (output_names is not None and root_names is not None)
        ):  # pragma: no cover
            msg = "Safety assertion failed, please report a bug to https://github.com/narwhals-dev/narwhals/issues"
            raise AssertionError(msg)

        return self.__class__(
            func,
            depth=self._depth + 1,
            function_name=f"{self._function_name}->{expr_name}",
            root_names=root_names,
            output_names=output_names,
            returns_scalar=self._returns_scalar or returns_scalar,
            backend_version=self._backend_version,
            version=self._version,
            kwargs=kwargs,
        )

    def __add__(self, other: DuckDBExpr) -> Self:
        return self._from_call(
            lambda _input, other: _input + other,
            "__add__",
            other=other,
            returns_scalar=False,
        )

    def __truediv__(self, other: DuckDBExpr) -> Self:
        return self._from_call(
            lambda _input, other: _input / other,
            "__truediv__",
            other=other,
            returns_scalar=False,
        )

    def __sub__(self, other: DuckDBExpr) -> Self:
        return self._from_call(
            lambda _input, other: _input - other,
            "__sub__",
            other=other,
            returns_scalar=False,
        )

    def __mul__(self, other: DuckDBExpr) -> Self:
        return self._from_call(
            lambda _input, other: _input * other,
            "__mul__",
            other=other,
            returns_scalar=False,
        )

    def __lt__(self, other: DuckDBExpr) -> Self:
        return self._from_call(
            lambda _input, other: _input < other,
            "__lt__",
            other=other,
            returns_scalar=False,
        )

    def __gt__(self, other: DuckDBExpr) -> Self:
        return self._from_call(
            lambda _input, other: _input > other,
            "__gt__",
            other=other,
            returns_scalar=False,
        )

    def __eq__(self, other: DuckDBExpr) -> Self:  # type: ignore[override]
        return self._from_call(
            lambda _input, other: _input == other,
            "__eq__",
            other=other,
            returns_scalar=False,
        )

    def alias(self, name: str) -> Self:
        def _alias(df: DuckDBInterchangeFrame) -> list[duckdb.Expression]:
            return [col.alias(name) for col in self._call(df)]

        # Define this one manually, so that we can
        # override `output_names` and not increase depth
        return self.__class__(
            _alias,
            depth=self._depth,
            function_name=self._function_name,
            root_names=self._root_names,
            output_names=[name],
            returns_scalar=self._returns_scalar,
            backend_version=self._backend_version,
            version=self._version,
            kwargs={**self._kwargs, "name": name},
        )

    def mean(self) -> Self:
        from duckdb import FunctionExpression

        return self._from_call(
            lambda _input: _input == FunctionExpression("mean", _input),
            "mean",
            returns_scalar=True,
        )

    def max(self) -> Self:
        from duckdb import FunctionExpression

        return self._from_call(
            lambda _input: _input == FunctionExpression("max", _input),
            "max",
            returns_scalar=True,
        )
