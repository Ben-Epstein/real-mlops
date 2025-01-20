MODEL (
    name sqlmesh_example.cust_cost_spread,
    kind INCREMENTAL_BY_TIME_RANGE(
        time_column ts
    ),
    cron '@daily',
    grain (id, ts),
    audits (assert_positive_order_ids),
    storage_format "columnstore",
    gateway duckdb
  );
  -- SELECT id, ts, part, value as v
  -- FROM mooncake.read_parquet('/workspace/ext_table1.parquet') AS (id int, ts timestamp, part int, value float)
  CALL postgres_execute(postgres, 'create extension if not exists pg_mooncake');
  CALL postgres_execute(postgres, 'SET default_table_access_method = ''columnstore''');


  SELECT part, ts, mean(value)*mean(value) as cust_cost_spread
  -- we cant read delta yet.. https://github.com/Mooncake-Labs/pg_mooncake/issues/99
  -- FROM mooncake.read_parquet('/workspace/ext_table1.parquet') as (id int, ts timestamp, part int, value float)
  FROM delta_scan('./ext_table2') as t2
  GROUP BY part, ts
  HAVING part < 4
  ORDER BY part, ts;

  
--   @upsert_delta()

  