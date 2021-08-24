# Beehive Data Export Tools

## Exporting Data Chunks from SDR

Just run the `export_data_chunks.py` tool with an optional `-m` measurements filter and start and end dates.

```sh
# ./export_data_chunks.py -m measurements startdate enddate
./export_data_chunks.py -m 'iio.*|env.*' 2021-01-01 2021-03-31
```

This will download, chunk and index data into `data/` for later compilation. Now you can create a `SAGE-Data.tar` bundle using:

```sh
./compile_bundle.py
```
