"""Prefect flows to populate sqlmesh models.

Check this out for better background tasks in fastapi (via prefect): https://github.com/PrefectHQ/prefect-background-task-examples/tree/main/fastapi-user-signups/fastapi_user_signups
"""

import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import duckdb
import polars as pl
from deltalake import DeltaTable
from prefect import flow, task

from features.constants import DEV, ENVIRONMENT

REPO_ROOT = Path(__file__).parent.parent.parent
SQLMESH_ROOT = REPO_ROOT / "src" / "features"
STREAMING_BATCH_SIZE = 50_000


def _tmp_product_raw_parquet() -> dict[Path, Path]:
    print("Creating tmp parquet files")
    parquet_locs = {}
    query_date = date.today() - timedelta(days=1)
    for table in [REPO_ROOT / "ext_table1.parquet", REPO_ROOT / "ext_table2.parquet"]:
        df1 = duckdb.query(
            f"SELECT i AS id, DATETIME '{query_date}' as ts, i % 2 AS part, i*2.5 AS value FROM range(0, 5) tbl(i)"
        ).pl()
        df2 = duckdb.query(
            f"SELECT i AS id, DATETIME '{query_date}' as ts, i % 2 AS part, i*3.2 AS value FROM range(5, 10) tbl(i)"
        ).pl()
        df = pl.concat([df1, df2])
        df.write_parquet(table)
        parquet_locs[table] = REPO_ROOT / Path(table).stem
    return parquet_locs


@task(log_prints=True)
def ingest_to_silver(parquet_maps: dict[Path, Path]) -> None:
    """Ingest raw data dump from client to silver delta lake."""
    # TODO: Read from root parquet, appent to ext_table1 and ext_table2
    for parquet_path, ext_table in parquet_maps.items():
        lazy_df = pl.scan_parquet(parquet_path)
        num_rows = lazy_df.select(pl.len()).collect().item()
        for batch_start in range(0, num_rows, STREAMING_BATCH_SIZE):
            chunk = lazy_df[batch_start : batch_start + STREAMING_BATCH_SIZE].collect(streaming=True)
            if DeltaTable.is_deltatable(str(ext_table)):
                chunk.write_delta(
                    ext_table,
                    mode="merge",
                    delta_merge_options={
                        "predicate": "s.ts = t.ts AND s.part = t.part",
                        "source_alias": "s",
                        "target_alias": "t",
                    },
                ).when_matched_update_all().when_not_matched_insert_all().execute()
            else:
                chunk.write_delta(ext_table)


# @task(log_prints=True)
# def run_sqlmesh(start_ds: date | None = None, end_ds: date | None = None) -> None:
#     """Run sqlmesh cron."""
# context = Context(paths=SQLMESH_ROOT, load=False)
# print("Running sqlmesh")
# TODO: In order to make this work, we turn off forking
# https://sqlmesh.readthedocs.io/en/stable/reference/configuration/?h=max+fork#parallel-loading
# check the performance implications, stick with CLI for now.
# res = context.run(
#     # TODO: dont ever default the environment
#     environment=os.getenv(ENVIRONMENT, DEV),
#     start=start_ds,
#     end=end_ds
# )
# assert res
# print("Done with sqlmesh")


@task(log_prints=True)
def run_sqlmesh(start_ds: date | None = None, end_ds: date | None = None) -> None:
    """Run sqlmesh cron.

    TODO: Check for pythonic sdk to do this.
    """
    env = os.getenv(ENVIRONMENT, DEV)
    cmd = f"sqlmesh -p {SQLMESH_ROOT} run {env}"
    if start_ds:
        cmd += f" -s {start_ds}"
    if end_ds:
        cmd += f" -e {end_ds}"
    print(f"Running sqlmesh with `{cmd}`")
    result = subprocess.run(cmd.split(" "), capture_output=True, text=True, check=False)
    if result.returncode == 0:
        print(f"SQLMesh ran successfully: {result.stdout}")
    else:
        raise RuntimeError(f"sqlmesh run failed for command {cmd}\n\n{result.stderr}")


@flow(name="Feature Store", log_prints=True)
def build_features(parquet_paths: dict[Path, Path], start_ds: date | None = None, end_ds: date | None = None) -> None:
    """Main flow. Run sqlmesh, migrate to gold."""
    ingest_to_silver(parquet_paths)
    run_sqlmesh(start_ds, end_ds)


if __name__ == "__main__":
    parquet_paths = _tmp_product_raw_parquet()
    build_features(parquet_paths)
