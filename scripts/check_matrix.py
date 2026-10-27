"""Run the release's declared CPython source matrix with registry dependencies."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def check(minor: str) -> None:
    command = [
        "uv", "run", "--no-project", "--no-sources",
        "--exclude-newer-package", "yidl=0 seconds",
        "--exclude-newer-package", "yidl-cache=0 seconds",
        "--env-file", ".release.env", "--python", minor,
        "--with", ".", "--with", "pytest==8.4.2", "--with", "black==26.3.1",
        "python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
    ]
    print(f"Checking CPython {minor}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    minors = config["tool"]["yidl"]["test-matrix"]["python"]
    with ThreadPoolExecutor(max_workers=len(minors)) as pool:
        list(pool.map(check, minors))
