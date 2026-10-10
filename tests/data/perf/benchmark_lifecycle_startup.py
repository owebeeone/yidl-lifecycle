"""Measure fresh-process Pyrolyze startup with automatic Lifecycle caching."""

from __future__ import annotations

import argparse
import builtins
import importlib
from importlib.util import find_spec
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter

MODES = ("disabled", "cold", "warm")
PLACEMENTS = ("override", "local", "home")
TK_MEMBERS = ("CFrame", "CLabel", "CButton", "CEntry", "CCombobox", "CTtkButton")


def probe(workload: str, mode: str, phases: bool) -> dict[str, object]:
    started = perf_counter()
    frontend = importlib.import_module("yidl_lifecycle.lifecycle")
    imported = perf_counter()
    timings: dict[str, float] = {}
    classes: list[str] = []
    generation_calls = 0
    original_generate = frontend._generate_lifecycle_ast
    original_decorate = frontend.lifecycle

    def timed(name, function):
        def call(*args, **kwargs):
            before = perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                timings[name] = timings.get(name, 0.0) + perf_counter() - before

        return call

    def generate(harvested):
        nonlocal generation_calls
        generation_calls += 1
        if mode == "warm":
            raise AssertionError("warm startup attempted lifecycle generation")
        return original_generate(harvested)

    def decorate(cls):
        classes.append(f"{cls.__module__}.{cls.__qualname__}")
        return original_decorate(cls)

    frontend._generate_lifecycle_ast = (
        timed("generation_ast", generate) if phases else generate
    )
    frontend.lifecycle = timed("decorators", decorate) if phases else decorate
    if phases:
        frontend.harvest_lifecycle_definition = timed(
            "harvesting", frontend.harvest_lifecycle_definition
        )
        frontend.compiled_lifecycle_code = timed(
            "lookup_and_producer", frontend.compiled_lifecycle_code
        )
        frontend.compile = timed("compilation", builtins.compile)

        def execute(code, namespace):
            timed("module_execution", builtins.exec)(code, namespace)
            namespace["build_lifecycle_class"] = timed(
                "class_build", namespace["build_lifecycle_class"]
            )

        frontend.exec = execute

    importlib.import_module("pyrolyze.runtime.context")
    if workload == "tk-six":
        module = importlib.import_module("pyrolyze.backends.tkinter.generated_library")
        for name in TK_MEMBERS:
            getattr(module.TkinterUiLibrary, name)
    elapsed = perf_counter() - started
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    counters = adapter.cache_statistics()
    diagnostics = adapter.cache_diagnostics()
    statistics_result = (
        None
        if counters is None
        else {
            "hits": counters.hits,
            "misses": counters.misses,
            "bypasses": counters.bypasses,
        }
    )
    if mode == "disabled":
        assert counters is None and generation_calls == len(classes)
    elif mode == "cold":
        assert counters is not None and counters.misses == len(classes)
        assert counters.hits == counters.bypasses == 0
        assert generation_calls == len(classes)
    else:
        assert counters is not None and counters.hits == len(classes)
        assert counters.misses == counters.bypasses == generation_calls == 0
        assert "yidl_lifecycle._generated_lifecycle_base" not in sys.modules
    native = sys.modules.get("astichi.lower_engine.native")
    selected_engine = (
        native.select_effective_lower_engine().selected_engine if native else None
    )
    if mode != "warm":
        assert selected_engine is not None and selected_engine.startswith("native")
    cache = adapter._cache
    dependency_files = (
        len(cache._dependencies.stamps)
        if cache is not None and cache._dependencies is not None
        else 0
    )
    if phases:
        timings["lookup_excluding_producer"] = (
            timings["lookup_and_producer"]
            - timings.get("generation_ast", 0.0)
            - timings.get("compilation", 0.0)
        )
    return {
        "seconds": elapsed,
        "adapter_import_seconds": imported - started,
        "generation_calls": generation_calls,
        "class_count": len(classes),
        "classes": classes,
        "cache": statistics_result,
        "locations": sorted({type(item.selected).__name__ for item in diagnostics}),
        "location_failures": sum(len(item.failures) for item in diagnostics),
        "dependency_files": dependency_files,
        "selected_engine": selected_engine,
        "generator_imported": "yidl_lifecycle._generated_lifecycle_base" in sys.modules,
        "timings": timings,
    }


def run_probe(
    workload: str, mode: str, sample: Path, placement: str, phases: bool
) -> dict[str, object]:
    env = dict(os.environ)
    env.pop("YIDL_LIFECYCLE_CACHE_DIR", None)
    env["YIDL_LIFECYCLE_CACHE"] = "off" if mode == "disabled" else "on"
    env["HOME"] = str(sample / "home")
    env["PYTHONPATH"] = os.pathsep.join(
        (str(sample / "src"), env.get("PYTHONPATH", ""))
    )
    env["ASTICHI_LOWER_ENGINE"] = "native"
    env["PYROLYZE_CONTEXT_IMPL"] = "lifecycle"
    if mode != "disabled" and placement == "override":
        env["YIDL_LIFECYCLE_CACHE_DIR"] = str(sample / "cache")
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--probe",
        workload,
        mode,
    ]
    if phases:
        command.append("--phases")
    started = perf_counter()
    result = subprocess.run(
        command, env=env, text=True, capture_output=True, timeout=60
    )
    if result.returncode:
        raise RuntimeError(f"{workload}/{mode}: {result.stdout}\n{result.stderr}")
    wall = perf_counter() - started
    row = json.loads(result.stdout.splitlines()[-1])
    row["process_wall_seconds"] = wall
    if mode != "disabled":
        expected = {
            "override": "ExplicitLocation",
            "local": "ModuleLocalLocation",
            "home": "MirroredSourceLocation",
        }[placement]
        assert row["locations"] == [expected], row
    return row


def prepare_sample(sample: Path, placement: str, workload: str) -> None:
    spec = find_spec("pyrolyze")
    assert spec is not None and spec.submodule_search_locations is not None
    source = Path(next(iter(spec.submodule_search_locations)))
    destination = sample / "src" / "pyrolyze"
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
    (sample / "home").mkdir()
    if placement == "home":
        # Simulate unusable local storage without changing system directories.
        parents = {path.parent for path in destination.rglob("*.py")}
        for parent in parents:
            pycache = parent / "__pycache__"
            pycache.mkdir()
            (pycache / "yidl_cache").write_text("blocked\n", encoding="utf-8")
    # Prime ordinary Python caches outside the timed samples, not generated code.
    run_probe(workload, "disabled", sample, placement, False)


def distribution(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def benchmark(
    workload: str, repeats: int, root: Path, placement: str
) -> dict[str, object]:
    directory = root / placement / workload
    directory.mkdir(parents=True)
    warm = directory / "populated"
    prepare_sample(warm, placement, workload)
    seed = run_probe(workload, "cold", warm, placement, False)
    samples: dict[str, list[dict[str, object]]] = {mode: [] for mode in MODES}
    for index in range(repeats):
        # Rotate order to avoid always measuring one configuration first.
        for mode in MODES[index % len(MODES) :] + MODES[: index % len(MODES)]:
            sample = directory / f"cold-{index}" if mode == "cold" else warm
            if mode == "cold":
                prepare_sample(sample, placement, workload)
            samples[mode].append(run_probe(workload, mode, sample, placement, False))
    phase_cold = directory / "phase-cold"
    prepare_sample(phase_cold, placement, workload)
    details = {
        mode: run_probe(
            workload,
            mode,
            phase_cold if mode == "cold" else warm,
            placement,
            True,
        )
        for mode in MODES
    }
    entries = tuple(warm.rglob("*.ycode"))
    summary = {
        mode: {
            "startup_seconds": distribution([row["seconds"] for row in rows]),
            "process_wall_seconds": distribution(
                [row["process_wall_seconds"] for row in rows]
            ),
            "adapter_import_seconds": distribution(
                [row["adapter_import_seconds"] for row in rows]
            ),
            "generation_calls": [row["generation_calls"] for row in rows],
            "cache": rows[0]["cache"],
        }
        for mode, rows in samples.items()
    }
    baseline = summary["disabled"]["startup_seconds"]["median"]
    cached = summary["warm"]["startup_seconds"]["median"]
    assert all(
        row["classes"] == seed["classes"] for rows in samples.values() for row in rows
    )
    return {
        "workload": workload,
        "placement": placement,
        "python": platform.python_version(),
        "platform": f"{sys.platform}-{platform.machine()}",
        "repeats": repeats,
        "class_count": seed["class_count"],
        "classes": seed["classes"],
        "cache_entries": len(entries),
        "cache_bytes": sum(path.stat().st_size for path in entries),
        "saved_seconds": baseline - cached,
        "speedup": baseline / cached,
        "summary": summary,
        "phase_probes": details,
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument(
        "--workloads",
        choices=("context", "tk-six"),
        nargs="+",
        default=["context", "tk-six"],
    )
    parser.add_argument("--probe", nargs=2, metavar=("WORKLOAD", "MODE"))
    parser.add_argument("--phases", action="store_true")
    parser.add_argument(
        "--placements", choices=PLACEMENTS, nargs="+", default=list(PLACEMENTS)
    )
    args = parser.parse_args()
    if args.probe:
        print(json.dumps(probe(*args.probe, args.phases)))
        return
    if args.repeats < 5:
        parser.error("use at least five fresh-process repetitions")
    with tempfile.TemporaryDirectory(prefix="lifecycle-startup-") as temporary:
        root = Path(temporary).resolve()
        for placement in args.placements:
            for workload in args.workloads:
                print(
                    json.dumps(benchmark(workload, args.repeats, root, placement)),
                    flush=True,
                )


if __name__ == "__main__":
    main()
