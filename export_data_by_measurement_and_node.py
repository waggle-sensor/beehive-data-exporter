#!/usr/bin/env python3
import argparse
from urllib.request import urlopen
import ssl
import time
import json
import gzip
from datetime import datetime, timedelta
import csv
import sys
from pathlib import Path


class QueryEncoder(json.JSONEncoder):
    
    def default(self, obj):
        if isinstance(obj, datetime):
             return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return json.JSONEncoder.default(self, obj)


def get_query_records(query):
    data = json.dumps(query, cls=QueryEncoder).encode()
    with urlopen("https://sdr.sagecontinuum.org/api/v1/query", data=data) as resp:
        return list(map(json.loads, resp))

# Python's time parser doesn't seem to support nanoseconds yet so this is a crude hack
# to round down to microseconds. We simply trucate to the first 26 characters like this:
# 2021-01-03T10:32:20.123456789Z ->
# 2021-01-03T10:32:20.123456xxxx ->
# |-------- 26 chars ------|
# 2021-01-03T10:32:20.123456Z
def round_down_to_microseconds(s):
    s = s[:26]
    if not s.endswith("Z"):
        s = s + "Z"
    return s


def time_since(t):
    return timedelta(seconds=time.time() - t)


def process_task(task):
    download_start_time = time.time()
    records = get_query_records(task["query"])
    download_duration = time_since(download_start_time)

    write_start_time = time.time()

    meta_headers = {k for r in records for k in r["meta"].keys()}
    meta_fields = sorted(meta_headers)

    tmpfile = task["path"].with_suffix(".tmp")
    tmpfile.parent.mkdir(parents=True, exist_ok=True)
    outfile = task["path"]
    outfile.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(tmpfile, "wt") as f:
        csvwriter = csv.writer(f)

        # write csv headers
        headers = ["name", "timestamp", "value"] + ["meta." + k for k in meta_fields]
        csvwriter.writerow(headers)

        # write all records with metadata in order of meta_fields
        for r in records:
            # NOTE(sean) We track timestamps at nanosecond granularity to future proof our pipeline. For now, we'll
            # trucate timestamps to microseconds because some languages may make it tricky to parse like Python.
            # 
            # I'm also separating presentation from uncertainty quantification, which we don't try to capture at all here.
            timestamp = round_down_to_microseconds(r["timestamp"])
            csvrow = [r["name"], timestamp, r["value"]] + [r["meta"].get(k) for k in meta_fields]
            csvwriter.writerow(csvrow)

    tmpfile.rename(outfile)

    write_duration = time_since(write_start_time)
    
    return {
        "task": task,
        "download_duration": str(download_duration),
        "write_duration": str(write_duration),
    }


def datetype(s):
    return datetime.strptime(s, "%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dates", nargs="*", type=datetype, help="dates to export")
    args = parser.parse_args()

    tasks = []

    for date in args.dates:
        for r in get_query_records({"start": date, "end": date + timedelta(days=1), "tail": 1}):
            tasks.append({
                "path": Path("data", r["name"], r["meta"]["node"], date.strftime("%Y-%m-%d.csv.gz")),
                "query": {
                    "start": date,
                    "end": date + timedelta(days=1),
                    "filter": {
                        "name": r["name"],
                        "node": r["meta"]["node"],
                    }
                },
            })

    for task in tasks:
        print(task)
        print(process_task(task))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
