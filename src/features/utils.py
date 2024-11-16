import os
from typing import Generator

import pandas as pd
import polars as pl
from deltalake import DeltaTable

from features.constants import ENVIRONMENT, PROD

PythonModelReturn = Generator[pd.DataFrame, None, None]


def yield_df(df: pl.DataFrame | pd.DataFrame) -> Generator[pd.DataFrame, None, None]:
    """Yield df from df if rows exist, else nothing.

    SQLMesh throws an error if you yield an empty df from a python function. So
    we are going to need this code everywhere.

    Usage: `yield from yield_df(final_df)`
    """
    if not len(df):
        yield from ()
    yield (df if isinstance(df, pd.DataFrame) else df.to_arrow())


def upsert_df_delta(df: pl.DataFrame, gold_delta_path: str, model_name: str) -> None:
    """Upsert the new model df. On conflict, update. On missing, add."""
    if os.getenv(ENVIRONMENT) != PROD:
        print("We are not in prod. Not syncing to delta lake.")
        return
    if df.is_empty():
        print("No data found in delta. Skipping")
        return
    table_uri = f"{gold_delta_path}/{model_name}"
    if DeltaTable.is_deltatable(table_uri):
        print(f"Table {table_uri} exists. Running merge-upsert on {len(df)} records.")
        df.write_delta(
            table_uri,
            mode="merge",
            delta_merge_options={
                "predicate": "s.ts = t.ts AND s.part = t.part",
                "source_alias": "s",
                "target_alias": "t",
            },
        ).when_matched_update_all().when_not_matched_insert_all().execute()
    else:
        print(f"Table {table_uri} does not exist. Creating table and inserting {len(df)} records")
        df.write_delta(table_uri)
