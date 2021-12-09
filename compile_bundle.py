#!/usr/bin/env python3
import argparse
import logging
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from shutil import copyfile, make_archive
from urllib.request import urlopen


def read_json_from_url(url):
    with urlopen(url) as f:
        return json.load(f)


def write_json_file(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"), sort_keys=True)


def clean_nodes(items):
    def valid_item(item):
        return item.get("vsn", "") != "" and item.get("node_id", "") != ""
    def clean_item(item):
        return {
            **item,
            "vsn": item["vsn"].upper(),
            "node_id": item["node_id"].lower(),
        }
    return [clean_item(item) for item in items if valid_item(item)]


def clean_ontology(items):
    def valid_item(item):
        return item.get("ontology", "") != ""
    def clean_item(item):
        return {
            **item,
            "description": item.get("description", ""),
            "unit": item.get("unit", ""),
            "units": item.get("units", ""),
        }
    return [clean_item(item) for item in items if valid_item(item)]


def write_human_readable_node_file(path, items):
    with open(path, "w") as outfile:
        print("# Node Metadata\n", file=outfile)
        for item in items:
            print("""VSN: {vsn}
Project: {project}
Location: {location}
Node Type: {node_type}
Has Shield: {shield}
Has Agent: {nx_agent}
Build Date: {build_date}
""".format(**item), file=outfile)


def write_human_readable_ontology_file(path, items):
    with open(path, "w") as outfile:
        print("# Ontology Metadata\n", file=outfile)
        for item in items:
            print("""Name: {ontology}
Description: {description}
Type: {unit}
Units: {units}
""".format(**item), file=outfile)


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

    write_json_file(workdir/"index.json", index)


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

    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S")

    template_context = {
        "creation_timestamp": datetime.now(),
    }

    with TemporaryDirectory() as rootdir:
        logging.info("populating new archive")

        # put items under SAGE-Data.date subdir to help avoid prevent untarring over existing data
        workdir = Path(rootdir, datetime.now().strftime("SAGE-Data.%Y-%m-%d"))
        workdir.mkdir(parents=True, exist_ok=True)

        logging.info("adding README")
        write_template("templates/README.md", workdir/"README.md", **template_context)
        
        logging.info("adding node metadata")
        nodes = clean_nodes(read_json_from_url("https://api.sagecontinuum.org/production"))
        write_json_file(workdir/"nodes.json", nodes)
        write_human_readable_node_file(workdir/"nodes.md", nodes)
        
        logging.info("adding ontology metadata")
        ontology = clean_ontology(read_json_from_url("https://api.sagecontinuum.org/ontology"))
        write_json_file(workdir/"ontology.json", ontology)
        write_human_readable_ontology_file(workdir/"ontology.md", ontology)
        
        logging.info("adding query executable")
        copyfile("query.py", workdir/"query.py")
        (workdir/"query.py").chmod(0o755)

        logging.info("adding data and index")
        build_data_and_index_files(args.datadir, workdir)

        logging.info("creating tar file")
        make_archive("SAGE-Data", "tar", rootdir, workdir.relative_to(rootdir))

        logging.info("done")


if __name__ == "__main__":
    main()
