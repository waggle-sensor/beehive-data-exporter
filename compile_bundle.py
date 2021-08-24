#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path
import re
from tarfile import TarFile
from tempfile import TemporaryDirectory
import json
from shutil import copyfile, make_archive


def build_data_and_index_files(datadir, workdir):
    index = []

    files = sorted(datadir.glob("**/*.ndjson.gz"))

    with (workdir/"data.ndjson.gz").open("wb") as f:
        for file in files:
            # read file data
            data = file.read_bytes()
            # read file index data
            key = json.loads(file.with_name(f"{file.name}.index").read_text())
            # track offset and append to data chunk
            offset = f.tell()
            size = f.write(data)

            index.append({
                "key": key,
                "offset": offset,
                "size": size,
            })

    with (workdir/"index.ndjson").open("w") as f:
        for item in index:
            json.dump(item, f, separators=(",", ":"))
            f.write("\n")


readme_template = """
# Sage Data Archive

https://sagecontinuum.org

Archive Creation Timestamp: {creation_timestamp}

... more text describing data...

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
"""


def repad(s):
    return s.strip() + "\n"


def write_template(path, template, *args, **kwargs):
    path.write_text(repad(template.format(*args, **kwargs)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datadir", default="data", type=Path, help="root data directory")
    parser.add_argument("-m", "--measurements", default="", help="regexp of measurements to include in bundle")
    # parser.add_argument("start_date", type=datetype, help="starting date to export")
    # parser.add_argument("end_date", type=datetype, help="ending date to export (inclusive)")
    args = parser.parse_args()

    creation_timestamp = datetime.now()

    with TemporaryDirectory() as rootdir:
        workdir = Path(rootdir, "SAGE-Data")
        workdir.mkdir(parents=True, exist_ok=True)

        write_template(workdir/"README.md", readme_template, creation_timestamp=creation_timestamp)
        build_data_and_index_files(args.datadir, workdir)

        # copy query script
        copyfile("query.py", workdir/"query.py")
        (workdir/"query.py").chmod(0o755)

        copyfile("variables.ndjson", workdir/"variables.ndjson")

        make_archive("SAGE-Data", "tar", rootdir, workdir.relative_to(rootdir))


if __name__ == "__main__":
    main()
