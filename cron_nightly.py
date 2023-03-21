import argparse
import logging
from exporter import exporter
from bundler import bundler
from datetime import datetime, timedelta
from pathlib import Path
import re
from shutil import move, rmtree


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

    logging.info("exporting %s to %s", start_date, end_date)

    exporter(
        start_date=start_date,
        end_date=end_date,
        include_re=re.compile("env.temperature|sys.uptime"),
    )

    for project in ["SAGE"]:
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

    # move all tar files into bundle dir
    bundle_dir = Path("bundles")

    try:
        rmtree(bundle_dir)
    except FileNotFoundError:
        pass

    bundle_dir.mkdir(parents=True, exist_ok=True)

    for path in Path(".").glob("*.tar"):
        move(path, bundle_dir)


if __name__ == "__main__":
    main()
