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

## Record Format

Records are provided as newline delimited JSON. This means each contains a single record encoded as a single valid JSON object.

Each record will contains the following core fields:

* `name` - Name of record.
* `timestamp` - Timestamp of record (UTC).
* `value` - Value of record.
* `meta` - Metadata tags of record.

Each record will also always have the following system provided metadata fields.

* `vsn` - VSN of node which produced record.
* `node` - Node ID of node which produced record.
* `host` - Compute device in node which produced record. (nxcore, nxagent, rpi or dellblade)
* `job` - Job which produced record.
* `task` - Task which produced record.
* `plugin` - Plugin which produced record.

Each record may contain additional application specific metadata fields.

The following is a sample of three records:

```txt
{"meta":{"host":"000048b02d15bc77.ws-nxcore","job":"cloud-cover-top","node":"000048b02d15bc77","plugin":"registry.sagecontinuum.org/seonghapark/cloud-cover:0.1.3","task":"cloud-cover-top","vsn":"W021"},"name":"env.coverage.cloud","timestamp":"2023-01-01T00:01:11.701769Z","value":0.44126666666666664}
{"meta":{"host":"000048b02d15bc77.ws-nxcore","job":"cloud-cover-top","node":"000048b02d15bc77","plugin":"registry.sagecontinuum.org/seonghapark/cloud-cover:0.1.3","task":"cloud-cover-top","vsn":"W021"},"name":"env.coverage.cloud","timestamp":"2023-01-01T00:10:42.471485Z","value":0.9982666666666666}
{"meta":{"host":"000048b02d15bc77.ws-nxcore","job":"cloud-cover-top","node":"000048b02d15bc77","plugin":"registry.sagecontinuum.org/seonghapark/cloud-cover:0.1.3","task":"cloud-cover-top","vsn":"W021"},"name":"env.coverage.cloud","timestamp":"2023-01-01T00:27:29.454493Z","value":0.9987555555555555}
```

When pretty printed, the first record above looks like:

```json
{
  "meta": {
    "host": "000048b02d15bc77.ws-nxcore",
    "job": "cloud-cover-top",
    "node": "000048b02d15bc77",
    "plugin": "registry.sagecontinuum.org/seonghapark/cloud-cover:0.1.3",
    "task": "cloud-cover-top",
    "vsn": "W021"
  },
  "name": "env.coverage.cloud",
  "timestamp": "2023-01-01T00:01:11.701769Z",
  "value": 0.44126666666666664
}
```

## Usage Examples

### Querying Data

Data can be queried with the included `query.py` script by providing a list of `meta=pattern` query terms. Any meta field may be used as a search parameter. Here are a few simple examples:

1. Find all data from for env.* sensors.

```sh
./query.py 'name=env.*'
```

2. Find all data from BME680 sensors.

```sh
./query.py 'sensor=bme680'
```

3. Find all data from raingauge task.

```sh
./query.py 'task=raingauge'
```

### Integration with Sage Data Client

This data archive can be used with our [Sage Data Client](https://github.com/sagecontinuum/sage-data-client) tool as follows.

First, extract some subset of the data to a file:

```sh
./query.py 'sensor=bme680' > sample.ndjson
```

Now, use the `sage_data_client.load` function to open it as a data frame:

```python
import sage_data_client

df = sage_data_client.load("sample.ndjson")
```

### Extracting All Records

Finally, the entire data file `data.ndjson.gz` can always be decompressed directly using `gzip -d data.ndjson.gz`.

We generally do *not* recommend this as the primary way to use this data. If you are exploring a small subset of the
data then using the included `query.py` script will likely be much faster and require less significantly less storage.
