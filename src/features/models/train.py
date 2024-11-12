from datetime import datetime
from typing import Any

import polars as pl
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from features.utils import PythonModelReturn, upsert_df_delta, yield_df

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
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="ts"),
    # table_format="delta",
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    *,
    gold_delta_uri: str,
    custom_mult: int = 1,
    must_have_data: bool = True,
    **kwargs: Any,
) -> PythonModelReturn:
    """Create the training table with prediction col."""
    mean_cust_ret = context.table("sqlmesh_example.mean_cust_retention")
    cust_cost_spread = context.table("sqlmesh_example.cust_cost_spread")
    WHERE_CLAUSE = f"where ts >= TIMESTAMP '{start}' and ts <= TIMESTAMP '{end}'"
    df1 = pl.DataFrame(context.fetchdf(f"SELECT * FROM {mean_cust_ret} {WHERE_CLAUSE}"))
    df2 = pl.DataFrame(context.fetchdf(f"SELECT * FROM {cust_cost_spread} {WHERE_CLAUSE}"))
    merged = df1.join(df2, on=["part", "ts"])
    merged = merged.with_columns(
        pl.when(merged["cust_cost_spread"] * custom_mult > MIN_CUST_COST, merged["mean_cust_retention"] < MAX_RET)
        .then(True)
        .otherwise(False)
        .alias("prediction")
    )
    yield from yield_df(merged)
    # Implicit post-statement
    upsert_df_delta(merged, gold_delta_uri, MODEL_NAME)
