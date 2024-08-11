# Narwhals

<h1 align="center">
	<img
		width="400"
		alt="narwhals_small"
		src="https://github.com/narwhals-dev/narwhals/assets/33491632/26be901e-5383-49f2-9fbd-5c97b7696f27">
</h1>

[![PyPI version](https://badge.fury.io/py/narwhals.svg)](https://badge.fury.io/py/narwhals)
[![Downloads](https://static.pepy.tech/badge/narwhals/month)](https://pepy.tech/project/narwhals)

Extremely lightweight and extensible compatibility layer between dataframe libraries!

- **Full API support**: cuDF, Modin, pandas, Polars, PyArrow
- **Interchange-level support**: Ibis, Vaex, anything else which implements the DataFrame Interchange Protocol

Seamlessly support all, without depending on any!

- ✅ **Just use** a subset of **the Polars API**, no need to learn anything new
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

Get started!

- [Read the documentation](https://narwhals-dev.github.io/narwhals/)
- [Chat with us on Discord!](https://discord.gg/V3PqtB4VA4)
- [Join our community call](https://calendar.google.com/calendar/embed?src=27ff6dc5f598c1d94c1f6e627a1aaae680e2fac88f848bda1f2c7946ae74d5ab%40group.calendar.google.com)
- [Read the contributing guide](https://github.com/narwhals-dev/narwhals/blob/main/CONTRIBUTING.md)

## Used by / integrates with

Join the party!

- [Altair](https://github.com/vega/altair/)
- [Hamilton](https://github.com/DAGWorks-Inc/hamilton/tree/main/examples/narwhals)
- [scikit-lego](https://github.com/koaning/scikit-lego)
- [scikit-playtime](https://github.com/koaning/scikit-playtime)
- [timebasedcv](https://github.com/FBruzzesi/timebasedcv)

Feel free to add your project to the list if it's missing, and/or
[chat with us on Discord](https://discord.gg/V3PqtB4VA4) if you'd like any support.

## Installation

- pip (recommended, as it's the most up-to-date)
  ```
  pip install narwhals
  ```
- conda-forge (also fine, but the latest version may take longer to appear)
  ```
  conda install -c conda-forge narwhals
  ```

## Usage

There are three steps to writing dataframe-agnostic code using Narwhals:

1. use `narwhals.from_native` to wrap a pandas/Polars/Modin/cuDF/PyArrow
   DataFrame/LazyFrame in a Narwhals class
2. use the [subset of the Polars API supported by Narwhals](https://narwhals-dev.github.io/narwhals/api-reference/)
3. use `narwhals.to_native` to return an object to the user in its original
   dataframe flavour. For example:

   - if you started with pandas, you'll get pandas back
   - if you started with Polars, you'll get Polars back
   - if you started with Modin, you'll get Modin back (and compute will be distributed)
   - if you started with cuDF, you'll get cuDF back (and compute will happen on GPU)
   - if you started with PyArrow, you'll get PyArrow back

## Example

See the [tutorial](https://narwhals-dev.github.io/narwhals/basics/dataframe/) for several examples!

## Scope

- Do you maintain a dataframe-consuming library?
- Do you have a specific Polars function in mind that you would like Narwhals to have in order to make your work easier?

If you said yes to both, we'd love to hear from you!

**Note**: You might suspect that this is a secret ploy to infiltrate the Polars API everywhere.
Indeed, you may suspect that.

## Sponsors and institutional partners

Narwhals is 100% independent, community-driven, and community-owned.
We are extremely grateful to the following organisations for having
provided some funding / development time:

- [Quansight Labs](https://labs.quansight.org)
- [Quansight Futures](https://www.qi.ventures)
- [OpenTeams](https://www.openteams.com)
- [POSSEE initiative](https://possee.org)
- [BYU-Idaho](https://www.byui.edu)

If you contribute to Narwhals on your organization's time, please let us know. We'd be happy to add your employer
to this list!

## Why "Narwhals"?

[Coz they are so awesome](https://youtu.be/ykwqXuMPsoc?si=A-i8LdR38teYsos4).

Thanks to [Olha Urdeichuk](https://www.fiverr.com/olhaurdeichuk) for the illustration!
