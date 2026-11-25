#!/usr/bin/env python3
"""THE COMEBACK — make.fun news-image-20261124 entrypoint (stdlib only).

The repository holds the pre-rendered front page as entry.png in the repo
root. This program just copies it to the grader's output directory, exactly
like the kit's own starter main.ts does. Standard library only: no third-party packages,
no system fonts, no network. It runs twice and writes the same bytes both
times, as the competition requires.

  MAKEFUN_OUTPUT_DIR=out python3 main.py   # local check
  python3 main.py                          # sandbox: writes /output/entry.png
"""

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# entry.png lives in the repository root: beside this file, or one level up
# when this file is run from src/.
SRC = HERE / "entry.png"
if not SRC.is_file():
    SRC = HERE.parent / "entry.png"
OUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
OUT = OUT_DIR / "entry.png"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, OUT)
    print(f"entry.png: {OUT}  {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
