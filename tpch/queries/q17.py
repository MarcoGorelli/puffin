import narwhals as nw
from narwhals.typing import FrameT


@nw.narwhalify
def query(lineitem_ds: FrameT, part_ds: FrameT) -> FrameT:
    var1 = "Brand#23"
    var2 = "MED BOX"

    query1 = (
        part_ds.filter(nw.col("p_brand") == var1)
        .filter(nw.col("p_container") == var2)
        .join(lineitem_ds, how="left", left_on="p_partkey", right_on="l_partkey")
    )

    return (
        query1.group_by("p_partkey")
        .agg((0.2 * nw.col("l_quantity").mean()).alias("avg_quantity"))
        .select(nw.col("p_partkey").alias("key"), nw.col("avg_quantity"))
        .join(query1, left_on="key", right_on="p_partkey")
        .filter(nw.col("l_quantity") < nw.col("avg_quantity"))
        .select((nw.col("l_extendedprice").sum() / 7.0).round(2).alias("avg_yearly"))
    )
