from datetime import datetime
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory

def repad(s):
    return s.strip() + "\n"

def write_template(path, template, *args, **kwargs):
    path.write_text(repad(template.format(*args, **kwargs)))

readme_template = """
# Sage Data Archive

Archive Creation Timestamp: {creation_timestamp}

... more text describing data...
"""

creation_timestamp = datetime.now()

with TemporaryDirectory() as tmp:
    write_template(Path(tmp, "README.md"), readme_template, creation_timestamp=creation_timestamp)

    with TarFile("data.tar", mode="w") as tar:
        # add metadata files
        tar.add(Path(tmp, "README.md"), "SAGE-Data/README.md")
        # add data files
        for p in sorted(Path("data").glob("**/*.csv.gz")):
            tar.add(p, arcname=Path("SAGE-Data", p))
