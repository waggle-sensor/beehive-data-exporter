#!/usr/bin/env python3
import argparse
import logging
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from shutil import copyfile, make_archive
from urllib.request import urlopen
import re
from string import Template


__all__ = ["bundler"]


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
            "project": item.get("project") or "",
            "commission_date": item.get("commission_date") or "",
            "retire_date": item.get("retire_date") or "",
        }
    return [clean_item(item) for item in items if valid_item(item)]


def clean_ontology(items):
    def valid_item(item):
        return item.get("ontology", "") != ""
    def clean_item(item):
        return {
            **item,
            "description": item.get("description") or "",
            "unit": item.get("unit") or "",
            "units": item.get("units") or "",
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
Commission Date: {commission_date}
Retire Date: {retire_date}
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


def build_data_and_index_files(datadir, workdir, publish_filter):
    index = []

    files = sorted(datadir.glob("**/data.ndjson.gz"))

    with (workdir/"data.ndjson.gz").open("wb") as f:
        for file in files:
            # read query metadata
            query = json.loads(file.with_name("query.json").read_text())

            # only include items matched by the publish filter
            if not publish_filter(query):
                logging.debug("skip query data: %s", query)
                continue
            logging.debug("add query data: %s", query)
            # read file data
            data = file.read_bytes()
            # track offset and append to data chunk
            offset = f.tell()
            size = f.write(data)

            index.append({
                "query": query,
                "offset": offset,
                "size": size,
            })

    write_json_file(workdir/"index.json", index)


def write_template(src, dst, **kwargs):
    template = Template(Path(src).read_text())
    output = template.substitute(**kwargs)
    dst.write_text(output)


def parse_optional_date(s):
    if s is None or s == "":
        return None
    return parse_date(s)


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")

# TODO configure using functional opts pattern? Example:
# bundler = Bundler().exclude("^sys.*").project("SAGE")

def bundler(
    bundle_name: str,
    bundle_year: int,
    bundle_month: int,
    data_dir: Path = Path("data"),
    include_re: re.Pattern = re.compile(""),
    exclude_re: re.Pattern = re.compile("^$"),
    project_re: re.Pattern = re.compile(""),
):
    assert data_dir.is_dir()

    template_context = {
        "creation_timestamp": datetime.now(),
    }

    archive_name = bundle_name + f"-{bundle_year:04d}-{bundle_month:02d}"

    with TemporaryDirectory() as rootdir:
        logging.info("populating new %s bundle", bundle_name)

        # put items under .date subdir to help avoid prevent untarring over existing data
        workdir = Path(rootdir, archive_name)
        workdir.mkdir(parents=True, exist_ok=True)

        logging.info("adding README")
        write_template("templates/README.md", workdir/"README.md", **template_context)

        logging.info("adding node metadata")
        nodes = clean_nodes(read_json_from_url("https://api.sagecontinuum.org/production"))
        # only include nodes which are part of project
        nodes = [node for node in nodes if project_re.match(node["project"])]
        write_json_file(workdir/"nodes.json", nodes)
        write_human_readable_node_file(workdir/"nodes.md", nodes)

        logging.info("adding ontology metadata")
        ontology = clean_ontology(read_json_from_url("https://api.sagecontinuum.org/ontology"))
        write_json_file(workdir/"ontology.json", ontology)
        write_human_readable_ontology_file(workdir/"ontology.md", ontology)

        logging.info("adding query executable")
        copyfile("query.py", workdir/"query.py")
        (workdir/"query.py").chmod(0o755)

        # build publish filter
        nodes_by_vsn = {node["vsn"]: node for node in nodes}

        # publish_filter will returns whether a given data chunk key should
        # be included in the bundle
        def publish_filter(query):
            name = query["filter"]["name"]
            date = datetime.strptime(query["start"], "%Y-%m-%d")
            try:
                node = nodes_by_vsn[query["filter"]["vsn"]]
            except KeyError:
                return False
            commission_date = parse_optional_date(node.get("commission_date"))
            retire_date = parse_optional_date(node.get("retire_date"))
            return all([
                # filter ontology names
                include_re.match(name) is not None,
                exclude_re.match(name) is None,

                # filter dates
                date.year == bundle_year,
                date.month == bundle_month,

                # filter commisioning / retire dates
                commission_date is not None and commission_date <= date,
                retire_date is None or date <= retire_date,
            ])

        logging.info("adding data and index")
        build_data_and_index_files(data_dir, workdir, publish_filter)

        logging.info("creating archive file %s", archive_name)
        make_archive(archive_name, "tar", rootdir, workdir.relative_to(rootdir))

        logging.info("finished creating %s bundle", bundle_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--datadir", default="data", type=Path, help="root data directory")
    parser.add_argument("--include", default="", type=re.compile, help="regexp of ontology to include in bundle")
    parser.add_argument("--exclude", default="^$", type=re.compile, help="regexp of ontology to exclude from bundle")
    parser.add_argument("--project", default="", type=re.compile, help="regexp of projects to include in bundle")
    parser.add_argument("bundle_name", help="name of output bundle")
    parser.add_argument("bundle_year", type=int, help="include data ending at enddate")
    parser.add_argument("bundle_month", type=int, help="include data ending at enddate")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S")

    try:
        bundler(
            bundle_name=args.bundle_name,
            bundle_year=args.bundle_year,
            bundle_month=args.bundle_month,
            data_dir=args.datadir,
            include_re=args.include,
            exclude_re=args.exclude,
            project_re=args.project,
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
