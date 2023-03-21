# Beehive Data Export Tools

## Exporting Data Chunks from SDR

Just run the `exporter.py` tool with an optional `--include` measurements filter and start and end dates.

```sh
./exporter.py --include 'iio.*|env.*' 2021-01-01 2021-03-31
```

This will download, chunk and index data into `data/` for later compilation. Now you can create a `SAGE-Data-2022-01.tar` bundle using:

```sh
./bundler.py SAGE-Data 2022 01
```

## Measurement Information

Detailed metadata is in the included `variables.ndjson` file. This file is a machine readable list of items
containing measurement names, descriptions and units. For example:

```
{"name":"env.raingauge.acc","description":"Rain gauge accumulation mm between measurements.","units":"mm"}
```
