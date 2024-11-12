AUDIT (
    name assert_positive_order_ids,
  );

  SELECT *
  FROM @this_model
  WHERE
    part < 0
  