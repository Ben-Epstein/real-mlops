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



# Dev notes

## Trying to setup s3 bucket mounting


https://bluexp.netapp.com/blog/amazon-s3-as-a-file-system

If this works on mac, it'll definitely work on linux...
s3-fuse: https://github.com/s3fs-fuse/s3fs-fuse/wiki/Installation-Notes

* macos first needs: 
  * `brew install automake libtool pkg-config gcc wget`
  * `brew install macfuse` 
```
export LDFLAGS="-L/usr/local/opt/openssl@3/lib"
export CPPFLAGS="-I/usr/local/opt/openssl@3/include"
export PKG_CONFIG_PATH="/usr/local/opt/openssl@3/lib/pkgconfig"

git clone https://github.com/s3fs-fuse/s3fs-fuse.git
cd s3fs-fuse/
./autogen.sh
./configure --prefix=/usr/local --with-openssl
make
sudo make install
```
Lots of outputs, don't worry about them as long as this returns a valid output: `which s3fs`

Run minio locally. Optionally install to mac with `mc` cli so you can interact with minio
```
brew install minio/stable/minio minio/stable/mc
```
Then run with docker:
```
docker run -d --name minio \
    -p 9000:9000 -p 9090:9090 \
    -e "MINIO_ROOT_USER=admin" \
    -e "MINIO_ROOT_PASSWORD=password" \
    quay.io/minio/minio server /data --console-address ":9090"
```
Create a bucket. You can do this at the webUI at `http://localhost:9000` or via mc
```
mc alias set local http://localhost:9000 admin password
mc mb local/client1
```
mount with:
```
s3fs client1 ./my-bucket \
  -o passwd_file=/dev/fd/0 \
  -o url=http://localhost:9000 \
  -o use_path_request_style <<< "admin:password"
```

Unmount with `umount ./my-bucket` on macos and `fusermount -u ./my-bucket`  on linux

You will probably get an error about enabling system extensions. You need to follow the instructions provided by MacOS carefully for this. Reboot as instructed into safety mode and enable. Then come back and run again:
```markdown
shut down your system. Then press and hold the Touch ID or power button to launch Startup Security Utility. In Startup Security Utility, enable kernel extensions from the Security Policy button.
```

### Demo

https://github.com/user-attachments/assets/ab0c83b5-04a1-4e8b-b4e9-f6cec8b0bec5




