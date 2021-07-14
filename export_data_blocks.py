#!/usr/bin/env python3
import argparse
from urllib.request import urlopen
import ssl
import time
import json
import gzip
from datetime import datetime, timedelta
import csv
import re
import sys
from pathlib import Path

# NOTE there are some complications with using CSV in this chunked way, unless we want
# to maintain a fixed global metadata list of what can be included
# metadata_schema = [
#     "node",
#     "plugin",
#     "camera"
# ]

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

    tmpfile = task["path"].with_suffix(".tmp")
    tmpfile.parent.mkdir(parents=True, exist_ok=True)
    outfile = task["path"]
    outfile.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(tmpfile, "wt") as f:
        for r in records:
            # flatten meta data for now. revisit whether we want to do this.
            for k, v in r["meta"].items():
                r[f"meta.{k}"] = v
            del r["meta"]
            r["timestamp"] = round_down_to_microseconds(r["timestamp"])
            print(json.dumps(r, separators=(",", ":")), file=f)

    tmpfile.rename(outfile)

    write_duration = time_since(write_start_time)
    
    return {
        "task": task,
        "download_duration": str(download_duration),
        "write_duration": str(write_duration),
    }


def datetype(s):
    return datetime.strptime(s, "%Y-%m-%d")


def daterange(start, end):
    date = start
    while date <= end:
        yield date
        date += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--measurements", default="", help="regexp of measurements to include in bundle")
    parser.add_argument("start_date", type=datetype, help="starting date to export")
    parser.add_argument("end_date", type=datetype, help="ending date to export (inclusive)")
    args = parser.parse_args()

    measurementsRE = re.compile(args.measurements)

    tasks = []

    for date in daterange(args.start_date, args.end_date):
        for r in get_query_records({"start": date, "end": date + timedelta(days=1), "tail": 1}):
            if not measurementsRE.match(r["name"]):
                continue
            tasks.append({
                "path": Path("data", date.strftime("%Y-%m-%d"), r["meta"]["plugin"], r["name"], r["meta"]["node"], date.strftime("%Y-%m-%d.json.gz")),
                "query": {
                    "start": date,
                    "end": date + timedelta(days=1),
                    "filter": {
                        "name": r["name"],
                        "node": r["meta"]["node"],
                        "plugin": r["meta"]["plugin"],
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
