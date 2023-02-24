#!/usr/bin/env python3
import argparse
from urllib.request import urlopen
import json
import gzip
from datetime import datetime, timedelta
import re
from pathlib import Path
import logging
from hashlib import sha1
from http import HTTPStatus
from urllib.error import HTTPError
import time
import os
from typing import NamedTuple

class Task(NamedTuple):
    path: Path
    query: dict
    index: str


DATA_QUERY_API_URL = os.getenv("DATA_QUERY_API_URL", "https://data.sagecontinuum.org/api/v1/query")


class DatetimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
             return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return json.JSONEncoder.default(self, obj)


def dump_json_normalized(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, cls=DatetimeEncoder)


def get_query_records(query):
    data = dump_json_normalized(query).encode()
    with urlopen(DATA_QUERY_API_URL, data=data) as resp:
        return list(map(json.loads, resp))


def get_query_records_with_retry(query):
    while True:
        try:
            return get_query_records(query)
        except HTTPError as e:
            if e.code == HTTPStatus.TOO_MANY_REQUESTS:
                time.sleep(0.2)
            else:
                raise


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


def process_task(task: Task):
    outfile = task.path
    outfile.parent.mkdir(parents=True, exist_ok=True)

    # download results from data api
    download_start_time = datetime.now()
    records = get_query_records_with_retry(task.query)
    download_duration = datetime.now() - download_start_time

    # write results
    write_start_time = datetime.now()
    tmpfile = outfile.with_suffix(".tmp")

    with gzip.open(tmpfile, "wt") as f:
        for r in records:
            r["timestamp"] = round_down_to_microseconds(r["timestamp"])
            print(dump_json_normalized(r), file=f)

    tmpfile.rename(outfile)

    write_duration = datetime.now() - write_start_time

    queryfile = outfile.with_name("query.json")
    queryfile.write_text(dump_json_normalized(task.query))

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
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--datadir", default="data", type=Path, help="root data directory")
    parser.add_argument("--include", default="", help="regexp of measurements to include in bundle")
    parser.add_argument("--exclude", default="^$", help="regexp of measurements to exclude from bundle")
    parser.add_argument("start_date", type=datetype, help="starting date to export")
    parser.add_argument("end_date", type=datetype, help="ending date to export (inclusive)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(message)s",
                        datefmt="%Y/%m/%d %H:%M:%S")

    includeRE = re.compile(args.include)
    excludeRE = re.compile(args.exclude)

    for date in daterange(args.start_date, args.end_date):
        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%d")

        donefile = Path(args.datadir, year, month, day, ".done")

        if donefile.exists():
            logging.debug("already processed date %s", date)
            continue

        logging.info("processing date %s", date)

        # build task list
        tasks = []

        for r in get_query_records_with_retry({"start": date, "end": date + timedelta(days=1), "tail": 1}):
            if excludeRE.match(r["name"]):
                continue
            if not includeRE.match(r["name"]):
                continue
            # build filters to be used later
            filters = {}
            filters["name"] = r["name"]
            filters["date"] = date.strftime("%Y-%m-%d")
            for k, v in r["meta"].items():
                filters[k] = v
            index = dump_json_normalized(filters)
            chunk_id = sha1(index.encode()).hexdigest()

            query = {
                "start": date,
                "end": date + timedelta(days=1),
                "filter": {
                    "name": r["name"],
                }
            }

            for k, v in r["meta"].items():
                query["filter"][k] = v

            path = Path(args.datadir, year, month, day, r["name"], r["meta"]["vsn"], chunk_id, "data.ndjson.gz")

            # skip task if data file has already been created
            if path.exists():
                continue

            tasks.append(Task(
                path=path,
                query=query,
                index=index,
            ))

        # process task list
        for task in tasks:
            logging.info("processing task %s", task)
            process_task(task)

        donefile.parent.mkdir(parents=True, exist_ok=True)
        donefile.touch()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
