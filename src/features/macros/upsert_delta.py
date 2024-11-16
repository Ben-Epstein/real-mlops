import os

import duckdb
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator

from features.constants import DB_URI_VAR, ENVIRONMENT, GOLD_DELTA_URI_VAR, PROD
from features.utils import upsert_df_delta


@macro(metadata_only=True)
def upsert_delta(evaluator: MacroEvaluator) -> str:
    """Take the latest records produced by SQL models and upsert them to their reflected gold delta table."""
    if evaluator.runtime_stage == "evaluating" and os.getenv(ENVIRONMENT) == PROD:
        gold_delta_uri = evaluator.var(GOLD_DELTA_URI_VAR)
        db_uri = evaluator.var(DB_URI_VAR)
        con = duckdb.connect(db_uri)
        start_ts = evaluator.locals["start_ts"]
        end_ts = evaluator.locals["end_ts"]
        model_name = evaluator.locals["snapshot"].node.name
        table = evaluator.locals["this_model"].replace('"', "").lstrip("db.")
        data = con.query(
            f"select * from {table} where ts >= TIMESTAMP '{start_ts}' and ts <= TIMESTAMP '{end_ts}'"
        ).pl()
        upsert_df_delta(data, gold_delta_uri, model_name)
    return "values(1)"
