from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import sys

from yidl.concept_parser import compile_yidl_files
from yidl.generation.data_def_sys import emit_concept_runtime_source


_PACKAGE_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_ROOT.parent.parent
_YIDL_SOURCE_DIR = _PACKAGE_ROOT / "yidl"
_GENERATED_BASE_PATH = _PACKAGE_ROOT / "_generated_lifecycle_base.py"
_ENTRY_PATH = _YIDL_SOURCE_DIR / "lifecycle_base.yidl"
_CONCEPT_NAME = "LifecycleBase"


def render_lifecycle_base_source(
    *,
    source_dir: Path = _YIDL_SOURCE_DIR,
    entry_path: Path = _ENTRY_PATH,
    project_root: Path = _PROJECT_ROOT,
) -> str:
    """Render the generated lifecycle base from the checked-in YIDL layers."""

    paths = tuple(sorted(source_dir.glob("*.yidl")))
    compiled = compile_yidl_files(
        {
            path.relative_to(project_root).as_posix(): path.read_text(encoding="utf-8")
            for path in paths
        },
        entry_path.relative_to(project_root).as_posix(),
    )
    concept = compiled.concepts[_CONCEPT_NAME]
    return emit_concept_runtime_source(
        concept.plan.build_data_definition(),
        resources=concept.resources,
        assembly_plan=concept,
    )


def check_lifecycle_base(
    *,
    generated_path: Path = _GENERATED_BASE_PATH,
) -> tuple[bool, str]:
    """Return whether the committed generated base matches regenerated source."""

    expected = generated_path.read_text(encoding="utf-8")
    actual = render_lifecycle_base_source()
    if actual == expected:
        return True, ""
    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=generated_path.as_posix(),
            tofile="regenerated lifecycle base",
            lineterm="",
        ),
    )
    return False, diff


def write_lifecycle_base(
    *,
    generated_path: Path = _GENERATED_BASE_PATH,
) -> None:
    """Rewrite the committed generated base from the checked-in YIDL layers."""

    generated_path.write_text(render_lifecycle_base_source(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate or check src/yidl_lifecycle/_generated_lifecycle_base.py "
            "from src/yidl_lifecycle/yidl/*.yidl."
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite the generated lifecycle base instead of checking it",
    )
    args = parser.parse_args(argv)

    if args.write:
        write_lifecycle_base()
        print(f"wrote {_GENERATED_BASE_PATH.relative_to(_PACKAGE_ROOT.parent.parent)}")
        return 0

    ok, diff = check_lifecycle_base()
    if ok:
        print("generated lifecycle base matches")
        return 0
    print(diff, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
