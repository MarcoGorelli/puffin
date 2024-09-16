from queries import q13

from . import IO_FUNCS
from . import customer
from . import orders

tool = "pandas[pyarrow]"
fn = IO_FUNCS[tool]
print(q13.query(fn(customer), fn(orders)))

tool = "polars[lazy]"
fn = IO_FUNCS[tool]
print(q13.query(fn(customer), fn(orders)).collect())

tool = "pyarrow"
fn = IO_FUNCS[tool]
print(q13.query(fn(customer), fn(orders)))

tool = "dask"
fn = IO_FUNCS[tool]
print(q13.query(fn(customer), fn(orders)).compute())
