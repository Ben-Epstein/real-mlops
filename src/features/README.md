## Some commands

After running the migration:

`uv run sqlmesh fetchdf 'select * from sqlmesh_example.full_model'`

Or:
```py
import duckdb

con = duckdb.con("db.db")
df = con.execute("select * from sqlmesh_example.full_model").pl()
pl.write_delta("delta")

# now you can query delta with duckdb
df2 = duckdb.execute("select * from delta_scan('./delta')").pl()
```

## Questions
* How do I get sqlmesh to handle delta natively as my format? I feel like its all going into this `db.db` object, which seems unideal, right?
* How do I ingest the initial raw data? In this demo, I'm using a csv seed file which I don't like
  * I think the answer here is to use [external models](https://sqlmesh.readthedocs.io/en/stable/concepts/models/external_models). This is where prefect comes in at step 0 of the data pipeline, in that it loads in some external raw data, validates it, and then pushes it to our bronze raw delta tables with polars `df.write_delta` in an append/merge mode!
  * Theres also something about [table_format](https://sqlmesh.readthedocs.io/en/stable/concepts/models/overview/?h=parquet#table_format) and [physical_properties](https://sqlmesh.readthedocs.io/en/stable/concepts/models/overview/?h=parquet#physical_properties) but i'm not yet sure I get it...
  * Ideally we don't want to have to take the results and then manually copy them all back to _new_ files that are delta, as that seems really silly. This would seemingly really defeat the purpose.