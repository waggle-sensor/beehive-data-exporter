#!/usr/bin/env python3
import argparse
import logging
from exporter import exporter
from bundler import bundler
from datetime import datetime, timedelta
from pathlib import Path
import re
from shutil import move, rmtree
from os import getenv
import subprocess


DATA_DIR = getenv("DATA_DIR", "data")
UPLOAD_ADDR = getenv("UPLOAD_ADDR", "bebop.lcrc.anl.gov")
UPLOAD_USER = getenv("UPLOAD_USER", "svcwagglersync")
UPLOAD_KEY = getenv("UPLOAD_KEY", "~/.ssh/lcrc")
UPLOAD_DIR = Path(getenv("UPLOAD_DIR", "/home/svcwagglersync/waggle/public_html/sagedata/"))
PROJECTS = getenv("PROJECTS", "SAGE").split()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(message)s",
                        datefmt="%Y/%m/%d %H:%M:%S")

    # end at last day of previous month
    end_date = (datetime.today().replace(day=1) - timedelta(days=1)).date()

    # start at first day of previous month
    start_date = end_date.replace(day=1)

    logging.info("exporting data from %s to %s", start_date, end_date)

    # export all data between start and end date
    exporter(
        start_date=start_date,
        end_date=end_date,
    )

    # build project bundles
    for project in PROJECTS:
        logging.info("building bundles for project %s", project)

        # build science bundle (everything except system metrics)
        bundler(
            bundle_name=f"{project}-Science",
            bundle_year=start_date.year,
            bundle_month=start_date.month,
            exclude_re=re.compile("^sys.*"),
            project_re=re.compile(project),
        )

        # build system bundle (only system metrics)
        bundler(
            bundle_name=f"{project}-System",
            bundle_year=start_date.year,
            bundle_month=start_date.month,
            include_re=re.compile("^sys.*"),
            project_re=re.compile(project),
        )

    # upload bundles
    for path in Path(".").glob("*.tar"):
        subprocess.check_call([
            "rsync",
            "--verbose",
            "--archive",
            "--remove-source-files",
            "--stats",
            "-e",
            f"ssh -i {UPLOAD_KEY} -o StrictHostKeyChecking=no",
            f"{path}",
            f"{UPLOAD_USER}@{UPLOAD_ADDR}:{UPLOAD_DIR/path.name}"
        ])


if __name__ == "__main__":
    main()
