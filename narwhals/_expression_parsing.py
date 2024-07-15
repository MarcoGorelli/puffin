# Utilities for expression parsing
# Useful for backends which don't have any concept of expressions, such
# and pandas or PyArrow.
from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar
from typing import Union
from typing import cast
from typing import overload

from narwhals.dependencies import get_numpy
from narwhals.utils import flatten

if TYPE_CHECKING:
    from narwhals._arrow.dataframe import ArrowDataFrame
    from narwhals._arrow.expr import ArrowExpr
    from narwhals._arrow.namespace import ArrowNamespace
    from narwhals._arrow.series import ArrowSeries
    from narwhals._arrow.typing import IntoArrowExpr
    from narwhals._pandas_like.dataframe import PandasLikeDataFrame
    from narwhals._pandas_like.expr import PandasLikeExpr
    from narwhals._pandas_like.namespace import PandasLikeNamespace
    from narwhals._pandas_like.series import PandasLikeSeries
    from narwhals._pandas_like.typing import IntoPandasLikeExpr

    CompliantNamespace = Union[PandasLikeNamespace, ArrowNamespace]
    CompliantExpr = Union[PandasLikeExpr, ArrowExpr]
    IntoCompliantExpr = Union[IntoPandasLikeExpr, IntoArrowExpr]
    IntoCompliantExprT = TypeVar("IntoCompliantExprT", bound=IntoCompliantExpr)
    CompliantExprT = TypeVar("CompliantExprT", bound=CompliantExpr)
    CompliantSeries = Union[PandasLikeSeries, ArrowSeries]
    ListOfCompliantSeries = Union[list[PandasLikeSeries], list[ArrowSeries]]
    ListOfCompliantExpr = Union[list[PandasLikeExpr], list[ArrowExpr]]
    CompliantDataFrame = Union[PandasLikeDataFrame, ArrowDataFrame]

    T = TypeVar("T")


def evaluate_into_expr(
    df: CompliantDataFrame, into_expr: IntoCompliantExpr
) -> ListOfCompliantSeries:
    """Return list of raw columns."""
    expr = parse_into_expr(into_expr, namespace=df.__narwhals_namespace__())
    return expr._call(df)  # type: ignore[arg-type]


@overload
def evaluate_into_exprs(
    df: PandasLikeDataFrame,
    *exprs: IntoPandasLikeExpr,
    **named_exprs: IntoPandasLikeExpr,
) -> list[PandasLikeSeries]: ...


@overload
def evaluate_into_exprs(
    df: ArrowDataFrame,
    *exprs: IntoArrowExpr,
    **named_exprs: IntoArrowExpr,
) -> list[ArrowSeries]: ...


def evaluate_into_exprs(
    df: CompliantDataFrame,
    *exprs: IntoCompliantExprT,
    **named_exprs: IntoCompliantExprT,
) -> ListOfCompliantSeries:
    """Evaluate each expr into Series."""
    series: ListOfCompliantSeries = [  # type: ignore[assignment]
        item
        for sublist in [evaluate_into_expr(df, into_expr) for into_expr in flatten(exprs)]
        for item in sublist
    ]
    for name, expr in named_exprs.items():
        evaluated_expr = evaluate_into_expr(df, expr)
        if len(evaluated_expr) > 1:
            msg = "Named expressions must return a single column"  # pragma: no cover
            raise AssertionError(msg)
        series.append(evaluated_expr[0].alias(name))  # type: ignore[arg-type]
    return series


def maybe_evaluate_expr(
    df: CompliantDataFrame, expr: CompliantExpr | T
) -> ListOfCompliantSeries | T:
    """Evaluate `expr` if it's an expression, otherwise return it as is."""
    if hasattr(expr, "__narwhals_expr__"):
        expr = cast("CompliantExpr", expr)
        return expr._call(df)  # type: ignore[arg-type]
    return expr


@overload
def parse_into_exprs(
    *exprs: IntoPandasLikeExpr,
    namespace: PandasLikeNamespace,
    **named_exprs: IntoPandasLikeExpr,
) -> list[PandasLikeExpr]: ...


@overload
def parse_into_exprs(
    *exprs: IntoArrowExpr,
    namespace: ArrowNamespace,
    **named_exprs: IntoArrowExpr,
) -> list[ArrowExpr]: ...


def parse_into_exprs(
    *exprs: IntoCompliantExpr,
    namespace: CompliantNamespace,
    **named_exprs: IntoCompliantExpr,
) -> ListOfCompliantExpr:
    """Parse each input as an expression (if it's not already one). See `parse_into_expr` for
    more details."""
    out = [
        parse_into_expr(into_expr, namespace=namespace) for into_expr in flatten(exprs)
    ]
    for name, expr in named_exprs.items():
        out.append(parse_into_expr(expr, namespace=namespace).alias(name))
    return out  # type: ignore[return-value]


def parse_into_expr(
    into_expr: IntoCompliantExpr,
    *,
    namespace: CompliantNamespace,
) -> CompliantExpr:
    """Parse `into_expr` as an expression.

    For example, in Polars, we can do both `df.select('a')` and `df.select(pl.col('a'))`.
    We do the same in Narwhals:

    - if `into_expr` is already an expression, just return it
    - if it's a Series, then convert it to an expression
    - if it's a numpy array, then convert it to a Series and then to an expression
    - if it's a string, then convert it to an expression
    - else, raise
    """

    if hasattr(into_expr, "__narwhals_expr__"):
        return into_expr  # type: ignore[return-value]
    if hasattr(into_expr, "__narwhals_series__"):
        return namespace._create_expr_from_series(into_expr)  # type: ignore[arg-type]
    if isinstance(into_expr, str):
        return namespace.col(into_expr)
    if (np := get_numpy()) is not None and isinstance(into_expr, np.ndarray):
        series = namespace._create_compliant_series(into_expr)
        return namespace._create_expr_from_series(series)  # type: ignore[arg-type]
    msg = f"Expected IntoExpr, got {type(into_expr)}"  # pragma: no cover
    raise AssertionError(msg)


def reuse_series_implementation(
    expr: CompliantExprT,
    attr: str,
    *args: Any,
    returns_scalar: bool = False,
    **kwargs: Any,
) -> CompliantExprT:
    """Reuse Series implementation for expression.

    If Series.foo is already defined, and we'd like Expr.foo to be the same, we can
    leverage this method to do that for us.

    Arguments
        expr: expression object.
        attr: name of method.
        returns_scalar: whether the Series version returns a scalar. In this case,
            the expression version should return a 1-row Series.
        args, kwargs: arguments and keyword arguments to pass to function.
    """
    plx = expr.__narwhals_namespace__()

    def func(df: CompliantDataFrame) -> list[CompliantSeries]:
        out: list[CompliantSeries] = []
        for column in expr._call(df):  # type: ignore[arg-type]
            _out = getattr(column, attr)(
                *[maybe_evaluate_expr(df, arg) for arg in args],
                **{
                    arg_name: maybe_evaluate_expr(df, arg_value)
                    for arg_name, arg_value in kwargs.items()
                },
            )
            if returns_scalar:
                out.append(plx._create_series_from_scalar(_out, column))  # type: ignore[arg-type]
            else:
                out.append(_out)
        if expr._output_names is not None and (
            [s.name for s in out] != expr._output_names
        ):  # pragma: no cover
            msg = "Found invalid series name"
            raise ValueError(msg)
        return out

    # Try tracking root and output names by combining them from all
    # expressions appearing in args and kwargs. If any anonymous
    # expression appears (e.g. nw.all()), then give up on tracking root names
    # and just set it to None.
    root_names = copy(expr._root_names)
    output_names = expr._output_names
    for arg in list(args) + list(kwargs.values()):
        if root_names is not None and isinstance(arg, expr.__class__):
            if arg._root_names is not None:
                root_names.extend(arg._root_names)
            else:
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
        msg = "output_names and root_names are incompatible"
        raise ValueError(msg)

    return plx._create_expr_from_callable(  # type: ignore[return-value]
        func,  # type: ignore[arg-type]
        depth=expr._depth + 1,
        function_name=f"{expr._function_name}->{attr}",
        root_names=root_names,
        output_names=output_names,
    )


def reuse_series_namespace_implementation(
    expr: CompliantExprT, series_namespace: str, attr: str, *args: Any, **kwargs: Any
) -> CompliantExprT:
    """Just like `reuse_series_implementation`, but for e.g. `Expr.dt.foo` instead
    of `Expr.foo`.
    """
    plx = expr.__narwhals_namespace__()
    return plx._create_expr_from_callable(  # type: ignore[return-value]
        lambda df: [
            getattr(getattr(series, series_namespace), attr)(*args, **kwargs)
            for series in expr._call(df)  # type: ignore[arg-type]
        ],
        depth=expr._depth + 1,
        function_name=f"{expr._function_name}->{series_namespace}.{attr}",
        root_names=expr._root_names,
        output_names=expr._output_names,
    )


def is_simple_aggregation(expr: CompliantExpr) -> bool:
    """
    Check if expr is a very simple one, such as:

    - nw.col('a').mean()  # depth 1
    - nw.mean('a')  # depth 1
    - nw.len()  # depth 0

    as opposed to, say

    - nw.col('a').filter(nw.col('b')>nw.col('c')).max()

    because then, we can use a fastpath in pandas.
    """
    return expr._depth < 2
