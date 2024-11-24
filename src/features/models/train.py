from datetime import datetime
from typing import Any

import duckdb
import polars as pl
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from features.utils import PythonModelReturn, yield_df

MODEL_NAME = "sqlmesh_example.train"

MIN_CUST_COST = 1
MAX_RET = 5


@model(
    MODEL_NAME,
    columns={
        "part": "int",
        "ts": "datetime",
        "prediction": "bool",
    },
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="ts", batch_size=12, batch_concurrency=1),
    interval_unit="hour",
    cron="@daily",
    # table_format="delta",
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    *,
    gold_delta_uri: str,
    db_uri: str,
    custom_mult: int = 1,
    must_have_data: bool = True,
    **kwargs: Any,
) -> PythonModelReturn:
    """Create the training table with prediction col."""
    mean_cust_ret = context.table("sqlmesh_example.mean_cust_retention")
    cust_cost_spread = context.table("sqlmesh_example.cust_cost_spread")
    WHERE_CLAUSE = f"where ts >= TIMESTAMP '{start}' and ts <= TIMESTAMP '{end}'"
    con = duckdb.connect(db_uri)
    df1 = con.query(f"SELECT * FROM {mean_cust_ret} {WHERE_CLAUSE}").pl()
    df2 = con.query(f"SELECT * FROM {cust_cost_spread} {WHERE_CLAUSE}").pl()
    merged = df1.join(df2, on=["part", "ts"])
    merged = merged.with_columns(
        pl.when(merged["cust_cost_spread"] * custom_mult > MIN_CUST_COST, merged["mean_cust_retention"] < MAX_RET)
        .then(True)
        .otherwise(False)
        .alias("prediction")
    )
    yield from yield_df(merged)
    # Implicit post-statement
    # upsert_df_delta(merged, gold_delta_uri, MODEL_NAME)
