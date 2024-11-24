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

  SELECT t2.part, t2.ts, mean(t2.value) * mean(t2.value) as cust_cost_spread
  FROM delta_scan('./ext_table2') as t2
  GROUP BY t2.part, t2.ts
  HAVING t2.part < 3
  ORDER BY t2.part, t2.ts;

  
--   @upsert_delta()

  