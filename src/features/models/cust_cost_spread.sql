MODEL (
    name sqlmesh_example.cust_cost_spread,
    kind INCREMENTAL_BY_TIME_RANGE(
        time_column ts
    ),
    cron '@daily',
    grain (id, ts),
    audits (assert_positive_order_ids),
    storage_format "columnar",
  );

  SELECT part, ts, mean(value) * mean(value) as cust_cost_spread
  -- we cant read delta yet.. https://github.com/Mooncake-Labs/pg_mooncake/issues/99
  FROM mooncake.read_parquet('/workspace/ext_table1.parquet') as (id int, ts timestamp, part int, value float)
  GROUP BY part, ts
  HAVING part < 4
  ORDER BY part, ts;

  -- FROM delta_scan('./ext_table2') as t2

  
--   @upsert_delta()

  