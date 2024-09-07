from queries import q4

from . import IO_FUNCS
from . import line_item
from . import orders

tool = "pandas[pyarrow]"
fn = IO_FUNCS[tool]
print(q4.query(fn(line_item), fn(orders)))

tool = "polars[lazy]"
fn = IO_FUNCS[tool]
print(q4.query(fn(line_item), fn(orders)).collect())
