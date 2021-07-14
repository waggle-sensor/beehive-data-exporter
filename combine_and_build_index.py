#!/usr/bin/env python3
from pathlib import Path
import json


root = Path("data")

files = sorted(root.glob("**/*.json.gz"))

index = []

offset = 0

with Path("data.json.gz").open("wb") as f:
    for file in files:
        # slice metadata from path
        date = file.parent.parent.parent.parent.name
        plugin = file.parent.parent.parent.name
        name = file.parent.parent.name
        node = file.parent.name

        offset = f.tell()
        data = file.read_bytes()
        size = f.write(data)

        index.append({
            "key": {
                "date": date,
                "plugin": plugin,
                "name": name,
                "node": node,
            },
            "offset": offset,
            "size": size,
            "path": str(file.relative_to(root)),
        })


with Path("index.json").open("w") as f:
    json.dump(index, f, separators=(",", ":"))
