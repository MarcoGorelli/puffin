from queries import q3

from . import IO_FUNCS
from . import customer
from . import lineitem
from . import orders

tool = "pandas[pyarrow]"
fn = IO_FUNCS[tool]
print(q3.query(fn(customer), fn(lineitem), fn(orders)))

tool = "polars[lazy]"
fn = IO_FUNCS[tool]
print(q3.query(fn(customer), fn(lineitem), fn(orders)).collect())

tool = "pyarrow"
fn = IO_FUNCS[tool]
print(q3.query(fn(customer), fn(lineitem), fn(orders)))
