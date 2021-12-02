# Sage Data Archive

## Overview of Contents

This searchable archive contains data from Sage nodes. It is organized as follows:

* data.ndjson.gz - Data file containing gzipped, newline delimited JSON measurements.
* index.ndjson - Index file used by query.py to search the data file.
* nodes.ndjson - Node metadata as newline delimited JSON.
* ontology.ndjson - Measurement ontology metadata as newline delimited JSON.
* query.py - Query script for quickly finding relevant data. (See Querying Data section below.)

## Provenance Info

* Project URL: https://sagecontinuum.org
* Archive Creation Timestamp: {creation_timestamp}

## Querying Data

Data can be queried with `query.py` by providing a list of meta=pattern search terms. Any meta field may be used as a search parameter.

### Examples

1. Find all data from metsense plugins.

```sh
./query.py 'plugin=metsense'
```

2. Find all data from metsense plugins for specific node.

```sh
./query.py 'plugin=metsense' 'node=000048b02d15bc77'
```

3. Find all data from for env.* sensors.

```sh
./query.py 'name=env.*'
```

4. Find all data from BME680 sensors.

```sh
./query.py 'sensor=bme680'
```
