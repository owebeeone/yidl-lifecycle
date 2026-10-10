# Lifecycle Performance Fixtures

## Generated-Code Cache Startup

`benchmark_lifecycle_startup.py` compares real Pyrolyze context and Tk six-control
startup in fresh processes, with generated-code caching disabled, empty, and
populated. It runs at least five samples per configuration, verifies generation
and cache counters, and reports phase probes separately. It compares explicit-root,
automatic local, and automatic home-fallback placement. Each mode uses copied
Pyrolyze source and a temporary home; the active checkout and real home are not
cache destinations. It does not create a GUI.

Run from this repository after installing the application probe dependency:

```sh
uv pip install --python .venv/bin/python 'frozendict>=2,<3'
PYTHONPATH=src:../yidl-cache/src:../yidl/src:../astichi/src:../pyrolyze/src:../pyrolyze \
  .venv/bin/python tests/data/perf/benchmark_lifecycle_startup.py --repeats 5
```

The selected Python needs tkinter for the Tk workload, and Astichi's native
extension must be built. See [startup measurements](../../../dev-docs/LifecycleCodeCacheStartup.md)
for timing boundaries, reproducibility details, results, and limitations.
Use `--placements local` or `--placements home` for one automatic route, and
`--workloads context` for only the thirteen-class context import. Disabled probes
set the explicit off switch; cold probes use new roots, and warm probes forbid
generation in fresh processes.

## Constructor Throughput

This directory contains the checked-in generated source used by the gated
lifecycle constructor throughput comparison. The fixture keeps the timed loop
focused on object construction and excludes one-time YIDL assembly and source
generation cost.

Regenerate the lifecycle fixture after changes to
`src/yidl_lifecycle/yidl/lifecycle_base.yidl` or the
lifecycle source generator:

```sh
PYTHONPATH=../astichi/src uv run python tests/data/perf/generate_lifecycle_constructor_perf_fixture.py
```

Run the lifecycle-vs-dataclass constructor comparison:

```sh
PYTHONPATH=../astichi/src uv run --with pytest python tests/data/perf/run_lifecycle_constructor_perf_comparison.py
```

The comparison creates generated lifecycle classes and equivalent
`dataclasses.make_dataclass(..., slots=True)` classes for field group sizes
5, 10, and 15. Each size has the same number of plain fields, managed count
fields, and derived managed fields. The derived dataclass fields are initialized
in `__post_init__`; the lifecycle fields use generated parameterized
`default_factory` lowering.

The test is skipped during normal regression runs unless `YIDL_PERF_TESTS=1`
is set.
