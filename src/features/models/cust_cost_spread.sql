MODEL (
    name sqlmesh_example.cust_cost_spread,
    kind INCREMENTAL_BY_TIME_RANGE(
        time_column ts
    ),
    cron '@daily',
    grain (id, ts),
    audits (assert_positive_order_ids),
    table_format "delta",
  );

  SELECT part, ts, mean(value) * mean(value) as cust_cost_spread
  FROM delta_scan('./ext_table2')
  GROUP BY part, ts
  ORDER BY part, ts;

  
--   @upsert_delta()

  