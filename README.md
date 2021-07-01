# Beehive Data Export Tools

## Exporting SDR Data to CSVs

Just run the `export_data_by_measurement.py` tool with a list of dates.

```sh
./export_data_by_measurement.py 2021-07-01 2021-07-02 2021-07-03 ...
```

This will download and transform data into `measurements/name/date.csv.gz` files.
