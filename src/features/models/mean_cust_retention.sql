MODEL (
    name sqlmesh_example.mean_cust_retention,
    kind INCREMENTAL_BY_TIME_RANGE(
        time_column ts
    ),
    cron '@daily',
    grain (id, ts),
    audits (assert_positive_order_ids),
    storage_format "columnar",
  );

  SELECT part, ts, mean(value) * mean(value) as mean_cust_retention
  -- FROM delta_scan('./ext_table1')
  -- we cant read delta yet.. https://github.com/Mooncake-Labs/pg_mooncake/issues/99
  FROM mooncake.read_parquet('/workspace/ext_table1.parquet')
  GROUP BY part, ts
  ORDER BY part, ts;

--   @upsert_delta()