import argparse
import logging
from exporter import exporter
from bundler import bundler
from datetime import datetime, timedelta
from pathlib import Path
import re
from shutil import move


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(message)s",
                        datefmt="%Y/%m/%d %H:%M:%S")

    end_date = datetime.today()
    start_date = end_date - timedelta(days=1)

    exporter(
        start_date=start_date,
        end_date=end_date,
        include_re=re.compile("env.temperature|sys.uptime"),
    )

    for project in ["SAGE", "DAWN"]:
        bundler(
            bundle_name=f"{project}-Science",
            bundle_year=2023,
            bundle_month=3,
            exclude_re=re.compile("^sys.*"),
            project_re=re.compile(project),
        )

        bundler(
            bundle_name=f"{project}-System",
            bundle_year=2023,
            bundle_month=3,
            include_re=re.compile("^sys.*"),
            project_re=re.compile(project),
        )

    # move all tar files into bundle dir
    bundle_dir = Path("bundles")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for path in Path(".").glob("*.tar"):
        move(path, bundle_dir)


if __name__ == "__main__":
    main()
