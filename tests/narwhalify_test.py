from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import pandas as pd
import pytest

from tests.utils import nw

if TYPE_CHECKING:
    from narwhals.typing import DataFrame


def test_narwhalify() -> None:
    @nw.narwhalify
    def func(df: DataFrame) -> DataFrame:
        return df.with_columns(nw.all() + 1)

    df = pd.DataFrame({"a": [1, 2, 3]})
    result = func(df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))
    result = func(df=df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))


def test_narwhalify_called() -> None:
    @nw.narwhalify()
    def func(df: DataFrame, a: int = 1) -> DataFrame:
        return df.with_columns(nw.all() + a)

    df = pd.DataFrame({"a": [1, 2, 3]})
    result = func(df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))
    result = func(df=df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))
    result = func(a=1, df=df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))


def test_narwhalify_method() -> None:
    class Foo:
        @nw.narwhalify_method
        def func(self, df: DataFrame, a: int = 1) -> DataFrame:
            return df.with_columns(nw.all() + a)

    df = pd.DataFrame({"a": [1, 2, 3]})
    result = Foo().func(df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))
    result = Foo().func(a=1, df=df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))


def test_narwhalify_method_called() -> None:
    class Foo:
        @nw.narwhalify_method(eager_only=True)
        def func(self, df: DataFrame, a: int = 1) -> DataFrame:
            return df.with_columns(nw.all() + a)

    df = pd.DataFrame({"a": [1, 2, 3]})
    result = Foo().func(df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))
    result = Foo().func(df=df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))
    result = Foo().func(a=1, df=df)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"a": [2, 3, 4]}))


def test_narwhalify_method_invalid() -> None:
    class Foo:
        @nw.narwhalify_method(eager_only=True)
        def func(self) -> DataFrame:  # pragma: no cover
            return self  # type: ignore[return-value]

        @nw.narwhalify(eager_only=True)
        def fun2(self, df: Any) -> DataFrame:  # pragma: no cover
            return df  # type: ignore[no-any-return]

    with pytest.raises(TypeError):
        Foo().func()

    @nw.narwhalify_method(eager_only=True)
    def func(_df: Any, a: int = 1) -> DataFrame:  # pragma: no cover
        return a  # type: ignore[return-value]

    with pytest.raises(TypeError, match="is meant to be called"):
        func(pd.DataFrame(), a=pd.DataFrame())


def test_narwhalify_invalid() -> None:
    @nw.narwhalify(eager_only=True)
    def func() -> DataFrame:  # pragma: no cover
        return None  # type: ignore[return-value]

    with pytest.raises(TypeError):
        func()
