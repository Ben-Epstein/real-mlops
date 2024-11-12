import subprocess
from datetime import date, timedelta
from pathlib import Path

import duckdb
import polars as pl
from prefect import flow, task

SQLMESH_ROOT = Path(__file__).parent / "features"
STREAMING_BATCH_SIZE = 50_000


def _tmp_product_raw_parquet() -> dict[str, str]:
    parquet_locs = {}
    query_date = date.today() - timedelta(days=1)
    for table in ["parquet_1.parquet", "parquet_2.parquet"]:
        df1 = duckdb.query(
            f"SELECT i AS id, DATETIME '{query_date}' as ts, i % 2 AS part, i*2.5 AS value FROM range(0, 5) tbl(i)"
        ).pl()
        df2 = duckdb.query(
            f"SELECT i AS id, DATETIME '{query_date}' as ts, i % 2 AS part, i*3.2 AS value FROM range(5, 10) tbl(i)"
        ).pl()
        df = pl.concat([df1, df2])
        df.write_parquet(table)
        parquet_locs[table] = Path(table).name
    return parquet_locs


@task(log_prints=True)
def ingest_to_silver(parquet_maps: dict[str, str]) -> None:
    """Ingest raw data dump from client to silver delta lake."""
    # TODO: Read from root parquet, appent to ext_table1 and ext_table2
    for parquet_path, ext_table in parquet_maps.items():
        lazy_df = pl.scan_parquet(parquet_path)
        num_rows = lazy_df.select(pl.len()).collect().item()
        for batch_start in range(0, num_rows, STREAMING_BATCH_SIZE):
            chunk = lazy_df[batch_start : batch_start + STREAMING_BATCH_SIZE].collect(streaming=True)
            chunk.write_delta(ext_table, mode="append")


@task(log_prints=True)
def run_sqlmesh(start_ds: date | None = None, end_ds: date | None = None) -> None:
    """Run sqlmesh cron.

    TODO: Check for pythonic sdk to do this.
    """
    cmd = f"sqlmesh -p {SQLMESH_ROOT} run"
    if start_ds:
        cmd += f" -s {start_ds}"
    if end_ds:
        cmd += f" -e {end_ds}"
    print(f"Running sqlmesh with `{cmd}`")
    result = subprocess.run(cmd.split(" "), capture_output=True, text=True, check=False)
    print("SQLMesh Result:")
    print(result)


@flow(name="Feature Store", log_prints=True)
def build_features(parquet_paths: dict[str, str], start_ds: date | None = None, end_ds: date | None = None) -> None:
    """Main flow. Run sqlmesh, migrate to gold."""
    ingest_to_silver(parquet_paths)
    run_sqlmesh(start_ds, end_ds)


if __name__ == "__main__":
    parquet_paths = _tmp_product_raw_parquet()
    build_features(parquet_paths)
