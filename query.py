#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
import gzip


def fatal(msg):
    print(msg)
    sys.exit(1)


def read_index_file(path):
    data = Path(path).read_text()
    return list(map(json.loads, data.splitlines()))


def build_query_patterns(query):
    patterns = {}

    for s in args.query:
        m = re.match("([A-Za-z0-9]+)=(\S+)$", s)
        if m is None:
            raise ValueError(f"Invalid query {s!r}.")
        key, value = m.groups()
        pattern = re.compile(value)
        patterns[key] = pattern

    return patterns

parser = argparse.ArgumentParser()
parser.add_argument("--root", default=".", type=Path, help="root directory to work in")
parser.add_argument("query", nargs="*", help="query terms")
args = parser.parse_args()

patterns = build_query_patterns(args.query)

try:
    index = read_index_file(Path(args.root, "index.ndjson"))
except FileNotFoundError:
    fatal("no index.json file in data folder")
except json.JSONDecodeError:
    fatal("invalid index.ndjson file")

def item_matches_patterns(item, patterns):
    return all(k in item["key"] and pattern.search(item["key"][k]) for k, pattern in patterns.items())

selected_items = [item for item in index if item_matches_patterns(item, patterns)]

with Path(args.root, "data.ndjson.gz").open("rb") as f:
    for item in selected_items:
        f.seek(item["offset"])
        data = f.read(item["size"])
        sys.stdout.write(gzip.decompress(data).decode())

# TODO make this match data API...
