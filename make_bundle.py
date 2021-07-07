import argparse
from datetime import datetime
from pathlib import Path
import re
from tarfile import TarFile
from tempfile import TemporaryDirectory


readme_template = """
# Sage Data Archive

Archive Creation Timestamp: {creation_timestamp}

... more text describing data...
"""


def repad(s):
    return s.strip() + "\n"


def write_template(path, template, *args, **kwargs):
    path.write_text(repad(template.format(*args, **kwargs)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--measurements", default="", help="regexp of measurements to include in bundle")
    # parser.add_argument("start_date", type=datetype, help="starting date to export")
    # parser.add_argument("end_date", type=datetype, help="ending date to export (inclusive)")
    args = parser.parse_args()

    measurementsRE = re.compile(args.measurements)

    creation_timestamp = datetime.now()

    with TemporaryDirectory() as tmp:
        write_template(Path(tmp, "README.md"), readme_template, creation_timestamp=creation_timestamp)

        with TarFile("data.tar", mode="w") as tar:
            # add metadata files
            tar.add(Path(tmp, "README.md"), "SAGE-Data/README.md")
            # add data files
            for p in sorted(Path("data").glob("**/*.csv.gz")):
                if not measurementsRE.match(p.parent.parent.name):
                    continue
                tar.add(p, arcname=Path("SAGE-Data", p))


if __name__ == "__main__":
    main()
