from datetime import date, timedelta

import duckdb
import polars as pl
from deltalake import write_deltalake


def _generate_tables():
    query_date = date.today() - timedelta(days=1)
    for table in ["ext_table1", "ext_table2"]:
        df1 = duckdb.query(
            f"SELECT i AS id, DATETIME '{query_date}' as ts, i % 2 AS part, i*2.5 AS value FROM range(0, 5) tbl(i)"
        ).arrow()
        df2 = duckdb.query(
            f"SELECT i AS id, DATETIME '{query_date}' as ts, i % 2 AS part, i*3.2 AS value FROM range(5, 10) tbl(i)"
        ).arrow()
        write_deltalake(f"./{table}", df1, partition_by=["part"], mode="append")
        write_deltalake(f"./{table}", df2, partition_by=["part"], mode="append")


def mean_cust_retention() -> pl.DataFrame:
    return duckdb.execute("""SELECT part, mean(value) * mean(value) as mean_cust_retention
    FROM delta_scan('./ext_table1')
    GROUP BY part
    ORDER BY part;""").pl()


def cust_cost_spread() -> pl.DataFrame:
    return duckdb.execute("""SELECT part, max(value) * min(value) as cust_cost_spread
    FROM delta_scan('./ext_table2')
    GROUP BY part
    ORDER BY part;""").pl()


def transform(tb1: pl.DataFrame, tb2: pl.DataFrame) -> pl.DataFrame:
    merged = tb1.join(tb2, on="part")
    merged = merged.with_columns(
        (
            pl.when(merged["cust_cost_spread"] > 1, merged["mean_cust_retention"] < 5)
            .then(True)
            .otherwise(False)
            .alias("prediction")
        )
    )
    return merged


def flow() -> None:
    _generate_tables()
    res = transform(mean_cust_retention(), cust_cost_spread())
    res.write_delta("gold", mode="append")


_generate_tables()
