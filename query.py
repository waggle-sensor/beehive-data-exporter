#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
import gzip


def build_query_patterns(query):
    patterns = {}

    for s in query:
        m = re.match("([A-Za-z0-9]+)=(\S+)$", s)
        if m is None:
            raise ValueError(f"Invalid query {s!r}.")
        key, value = m.groups()
        pattern = re.compile(value)
        patterns[key] = pattern

    return patterns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path, help="root directory to work in")
    parser.add_argument("query", nargs="*", help="query terms")
    args = parser.parse_args()

    patterns = build_query_patterns(args.query)

    def item_matches_patterns(item, patterns):
        query_filter = item["query"]["filter"]
        return all(k in query_filter and pattern.search(query_filter[k]) for k, pattern in patterns.items())

    # get all matching items from index
    with Path(args.root, "index.ndjson").open("r") as f:
        matching_items = [item for item in map(json.loads, f) if item_matches_patterns(item, patterns)]

    # write gzip chunks corresponding to matching item
    with Path(args.root, "data.ndjson.gz").open("rb") as f:
        for item in matching_items:
            f.seek(item["offset"])
            data = f.read(item["size"])
            sys.stdout.write(gzip.decompress(data).decode())

    # TODO make this match data API...


if __name__ == "__main__":
    main()
