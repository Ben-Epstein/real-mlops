MODEL (
    name sqlmesh_example.mean_cust_retention,
    kind INCREMENTAL_BY_TIME_RANGE(
        time_column ts
    ),
    cron '@daily',
    grain (id, ts),
    audits (assert_positive_order_ids),
    table_format "delta",
  );

  SELECT part, ts, mean(value) * mean(value) as mean_cust_retention2
  FROM delta_scan('./ext_table1')
  GROUP BY part, ts
  ORDER BY part, ts;

--   @upsert_delta()