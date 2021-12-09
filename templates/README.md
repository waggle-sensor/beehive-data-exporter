# Sage Data Archive

## Overview of Contents

This searchable archive contains data from Sage nodes. It is organized as follows:

* data.ndjson.gz - Data file containing gzipped, newline delimited JSON measurements.
* query.py - Query script for seaching data. (See Querying Data section below.)
* index.json - Machine readable index file used by query script.
* nodes.md - Human readable version of node metadata.
* nodes.json - Machine readable node metadata.
* ontology.md - Human readable version of ontology metadata.
* ontology.json - Machine readable ontology metadata.

## Provenance Info

* Project URL: https://sagecontinuum.org
* Archive Creation Timestamp: {creation_timestamp}

## Querying Data

Data can be queried with `query.py` by providing a list of meta=pattern search terms. Any meta field may be used as a search parameter.

### Record Format

Records are provided as newline delimited JSON. This means each contains a single record encoded as a single valid JSON object.

Each record will contains the following core fields:

* `name` - Name of record.
* `timestamp` - Timestamp of record (UTC).
* `value` - Value of record.

Each record will also always have the following system provided metadata fields.

* `meta.vsn` - VSN of node which produced record.
* `meta.node` - Node ID of node which produced record.
* `meta.host` - Compute device in node which produced record. (nxcore, nxagent, rpi or dellblade)
* `meta.job` - Job which produced record.
* `meta.task` - Task which produced record.
* `meta.plugin` - Plugin which produced record.

Each record may contain additional application specific metadata fields.

The following is a sample of three records:

```txt
{{"timestamp":"2021-11-20T08:21:36.534437Z","name":"env.temperature","value":1.38,"meta.host":"000048b02d15bdd2.ws-nxcore","meta.job":"sage","meta.node":"000048b02d15bdd2","meta.plugin":"plugin-iio:0.4.5","meta.sensor":"bme280","meta.task":"iio-nx","meta.vsn":"W02D"}}
{{"timestamp":"2021-11-20T08:22:06.590439Z","name":"env.temperature","value":2.27,"meta.host":"000048b02d15bdd2.ws-nxcore","meta.job":"sage","meta.node":"000048b02d15bdd2","meta.plugin":"plugin-iio:0.4.5","meta.sensor":"bme280","meta.task":"iio-nx","meta.vsn":"W02D"}}
{{"timestamp":"2021-11-20T08:22:36.642844Z","name":"env.temperature","value":3.09,"meta.host":"000048b02d15bdd2.ws-nxcore","meta.job":"sage","meta.node":"000048b02d15bdd2","meta.plugin":"plugin-iio:0.4.5","meta.sensor":"bme280","meta.task":"iio-nx","meta.vsn":"W02D"}}
```

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
