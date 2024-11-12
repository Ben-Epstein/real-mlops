from datetime import datetime
from typing import Any

import polars as pl
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from features.utils import PythonModelReturn, upsert_df_delta, yield_df

MODEL_NAME = "sqlmesh_example.train"


@model(
    MODEL_NAME,
    columns={
        "part": "int",
        "ts": "datetime",
        "mean_cust_retention": "float",
        "cust_cost_spread": "float",
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
    custom_mult: int = 1,
    must_have_data: bool = True,
    gold_delta_path: str = "",
    **kwargs: Any,
) -> PythonModelReturn:
    breakpoint()
    if not gold_delta_path:
        raise ValueError("Python models must push results to gold delta lake")
    mean_cust_ret = context.table("sqlmesh_example.mean_cust_retention")
    cust_cost_spread = context.table("sqlmesh_example.cust_cost_spread")
    df1 = pl.DataFrame(context.fetchdf(f"SELECT * FROM {mean_cust_ret}"))
    df2 = pl.DataFrame(context.fetchdf(f"SELECT * FROM {cust_cost_spread}"))
    merged = df1.join(df2, on=["part", "ts"])
    merged = merged.with_columns(
        pl.when(merged["cust_cost_spread"] * custom_mult > 1, merged["mean_cust_retention"] < 5)
        .then(True)
        .otherwise(False)
        .alias("prediction")
    )
    yield from yield_df(merged)
    # Implicit post-statement
    upsert_df_delta(merged, gold_delta_path, MODEL_NAME)
