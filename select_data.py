#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
import gzip

parser = argparse.ArgumentParser()
parser.add_argument("--root", default=".", type=Path, help="root directory to work in")
parser.add_argument("--date", default="")
parser.add_argument("--node", default="")
parser.add_argument("--name", default="")
parser.add_argument("--plugin", default="")
args = parser.parse_args()

patterns = {
    "date": re.compile(args.date),
    "node": re.compile(args.node),
    "name": re.compile(args.name),
    "plugin": re.compile(args.plugin),
}

index = json.loads(Path(args.root, "index.json").read_text())

with Path(args.root, "data.json.gz").open("rb") as f:
    for item in index:
        if all(pattern.search(item["key"][k]) for k, pattern in patterns.items()):
            f.seek(item["offset"])
            data = f.read(item["size"])
            sys.stdout.write(gzip.decompress(data).decode())
