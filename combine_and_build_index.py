#!/usr/bin/env python3
import argparse
from pathlib import Path
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data", help="root data directory")
    # parser.add_argument("-m", "--measurements", default="", help="regexp of measurements to include in bundle")
    # parser.add_argument("start_date", type=datetype, help="starting date to export")
    # parser.add_argument("end_date", type=datetype, help="ending date to export (inclusive)")
    args = parser.parse_args()

    rootdir = Path(args.root)

    files = sorted(rootdir.glob("**/*.ndjson.gz"))

    index = []

    offset = 0

    with Path("data.ndjson.gz").open("wb") as f:
        for file in files:
            # slice metadata from path
            date = file.parent.parent.parent.parent.name
            plugin = file.parent.parent.parent.name
            name = file.parent.parent.name
            node = file.parent.name

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


    with Path("index.ndjson").open("w") as f:
        for item in index:
            json.dump(item, f, separators=(",", ":"))
            f.write("\n")

if __name__ == "__main__":
    main()