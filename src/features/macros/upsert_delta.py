import duckdb
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator

from features.config import DB_FILE
from features.utils import upsert_df_delta


@macro(metadata_only=True)
def upsert_delta(evaluator: MacroEvaluator, gold_delta_path: str):
    if evaluator.runtime_stage == "evaluating":
        con = duckdb.connect(DB_FILE)
        start_ts = evaluator.locals["start_ts"]
        end_ts = evaluator.locals["end_ts"]
        model_name = evaluator.locals["snapshot"].node.name
        table = evaluator.locals["this_model"].replace('"', "").lstrip("db.")
        data = con.query(f"select * from {table}").pl()
        upsert_df_delta(data, gold_delta_path, model_name)
