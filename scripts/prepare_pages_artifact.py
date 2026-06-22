#!/usr/bin/env python3
"""Stage GitHub Pages artifact with cheatSheet at root and under /cheatSheet/."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHEAT = ROOT / "cheatSheet"
OUT = ROOT / "_pages"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(CHEAT, OUT)
    shutil.copytree(CHEAT, OUT / "cheatSheet")
    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Prepared {OUT.relative_to(ROOT)} ({files} files)")


if __name__ == "__main__":
    main()
