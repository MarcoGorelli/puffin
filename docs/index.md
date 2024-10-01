# Narwhals

![](assets/image.png)

Extremely lightweight and extensible compatibility layer between dataframe libraries!

- **Full API support**: cuDF, Modin, pandas, Polars, PyArrow
- **Lazy-only support**: Dask
- **Interchange-level support**: Ibis, Vaex, anything else which implements the DataFrame Interchange Protocol

Seamlessly support all, without depending on any!

- ✅ **Just use** [a subset of **the Polars API**](https://narwhals-dev.github.io/narwhals/api-reference/), no need to learn anything new
- ✅ **Zero dependencies**, Narwhals only uses what
  the user passes in so your library can stay lightweight
- ✅ Separate **lazy** and eager APIs, use **expressions**
- ✅ Support pandas' complicated type system and index, without
  either getting in the way
- ✅ **100% branch coverage**, tested against pandas and Polars nightly builds
- ✅ **Negligible overhead**, see [overhead](https://narwhals-dev.github.io/narwhals/overhead/)
- ✅ Let your IDE help you thanks to **full static typing**, see [typing](https://narwhals-dev.github.io/narwhals/api-reference/typing/)
- ✅ **Perfect backwards compatibility policy**,
  see [stable api](https://narwhals-dev.github.io/narwhals/backcompat/) for how to opt-in

## Who's this for?

Anyone wishing to write a library/application/service which consumes dataframes, and wishing to make it
completely dataframe-agnostic.

Let's get started!
