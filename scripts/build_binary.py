from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SRC = ROOT / "src" / "__main__.py"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    shutil.rmtree(DIST, ignore_errors=True)
    run(
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--exclude-module",
        "pytest",
        "--exclude-module",
        "pytest_asyncio",
        "--exclude-module",
        "pytest_cov",
        "--exclude-module",
        "coverage",
        "--exclude-module",
        "tests",
        "--name",
        "rotranslator",
        str(SRC),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
