from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from narwhals._expression_parsing import maybe_evaluate_expr

if TYPE_CHECKING:
    from pyspark.sql import Column
    from typing_extensions import Self

    from narwhals._pyspark.dataframe import PySparkLazyFrame
    from narwhals._pyspark.namespace import PySparkNamespace


class PySparkExpr:
    def __init__(
        self,
        call: Callable[[PySparkLazyFrame], list[Column]],
        *,
        depth: int,
        function_name: str,
        root_names: list[str] | None,
        output_names: list[str] | None,
        # Whether the expression is a length-1 Series resulting from
        # a reduction, such as `nw.col('a').sum()`
        returns_scalar: bool,
    ) -> None:
        self._call = call
        self._depth = depth
        self._function_name = function_name
        self._root_names = root_names
        self._output_names = output_names
        self._returns_scalar = returns_scalar

    def __narwhals_expr__(self) -> None: ...

    def __narwhals_namespace__(self) -> PySparkNamespace:  # pragma: no cover
        # Unused, just for compatibility with PandasLikeExpr
        from narwhals._pyspark.namespace import PySparkNamespace

        return PySparkNamespace()

    @classmethod
    def from_column_names(cls: type[Self], *column_names: str) -> Self:
        def func(df: PySparkLazyFrame) -> list[Column]:
            from pyspark.sql import functions as F  # noqa: N812

            _ = df
            return [F.col(column_name) for column_name in column_names]

        return cls(
            func,
            depth=0,
            function_name="col",
            root_names=list(column_names),
            output_names=list(column_names),
            returns_scalar=False,
        )

    def _from_function(
        self,
        function: Callable[..., Column],
        expr_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        def func(df: PySparkLazyFrame) -> list[Column]:
            col_results = []
            inputs = self._call(df)
            _args = [maybe_evaluate_expr(df, x) for x in args]
            _kwargs = {
                key: maybe_evaluate_expr(df, value) for key, value in kwargs.items()
            }
            for _input in inputs:
                col_result = function(_input, *_args, **_kwargs)
                col_results.append(col_result)
            return col_results

        # Try tracking root and output names by combining them from all
        # expressions appearing in args and kwargs. If any anonymous
        # expression appears (e.g. nw.all()), then give up on tracking root names
        # and just set it to None.
        root_names = copy(self._root_names)
        output_names = self._output_names
        for arg in list(args) + list(kwargs.values()):
            if root_names is not None and isinstance(arg, self.__class__):
                if arg._root_names is not None:
                    root_names.extend(arg._root_names)
                else:  # pragma: no cover
                    # TODO(unassigned): increase coverage
                    root_names = None
                    output_names = None
                    break
            elif root_names is None:  # pragma: no cover
                # TODO(unassigned): increase coverage
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
            returns_scalar=False,
        )

    def __and__(self, other: PySparkExpr) -> Self:
        return self._from_function(
            lambda _input, other: _input.__and__(other), "__and__", other
        )

    def __gt__(self, other: PySparkExpr) -> Self:
        return self._from_function(
            lambda _input, other: _input.__gt__(other), "__gt__", other
        )

    def alias(self, name: str) -> Self:
        def func(df: PySparkLazyFrame) -> list[Column]:
            return [col_.alias(name) for col_ in self._call(df)]

        # Define this one manually, so that we can
        # override `output_names` and not increase depth
        return self.__class__(
            func,
            depth=self._depth,
            function_name=self._function_name,
            root_names=self._root_names,
            output_names=[name],
            returns_scalar=False,
        )
