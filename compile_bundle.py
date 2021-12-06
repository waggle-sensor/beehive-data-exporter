#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from shutil import copyfile, make_archive
from urllib.request import urlopen


def get_node_metadata():
    with urlopen("https://api.sagecontinuum.org/production") as f:
        items = json.load(f)

    # drop items without vsn
    items = [item for item in items if item["vsn"] != "" and item.get("node_id", "") != ""]

    return [{
        "vsn": item["vsn"].upper(),
        "node_id": item["node_id"].lower(),
        "location": item.get("location", ""),
        "project": item.get("project", ""),
    }
    for item in items
    if item["vsn"] != "" and item.get("node_id", "") != ""]


def download_node_metadata(path):
    items = get_node_metadata()
    with open(path, "w") as f:
        for item in items:
            print(json.dumps(item, sort_keys=True, separators=(",", ":")), file=f)


def download_ontology_metadata(path):
    with urlopen("https://api.sagecontinuum.org/ontology") as f:
        items = json.load(f)
    with open(path, "w") as f:
        for item in items:
            print(json.dumps(item, sort_keys=True, separators=(",", ":")), file=f)


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


def write_template(src, dst, *args, **kwargs):
    template = Path(src).read_text()
    output = template.format(*args, **kwargs)
    dst.write_text(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datadir", default="data", type=Path, help="root data directory")
    parser.add_argument("-m", "--measurements", default="", help="regexp of measurements to include in bundle")
    # parser.add_argument("start_date", type=datetype, help="starting date to export")
    # parser.add_argument("end_date", type=datetype, help="ending date to export (inclusive)")
    args = parser.parse_args()

    template_context = {
        "creation_timestamp": datetime.now(),
    }

    with TemporaryDirectory() as rootdir:
        workdir = Path(rootdir, "SAGE-Data")
        workdir.mkdir(parents=True, exist_ok=True)
        write_template("templates/README.md", workdir/"README.md", **template_context)
        build_data_and_index_files(args.datadir, workdir)
        download_node_metadata(workdir/"nodes.ndjson")
        download_ontology_metadata(workdir/"ontology.ndjson")
        copyfile("query.py", workdir/"query.py")
        (workdir/"query.py").chmod(0o755)
        make_archive("SAGE-Data", "tar", rootdir, workdir.relative_to(rootdir))


if __name__ == "__main__":
    main()
