# Lifecycle Cache Startup Measurements

## Historical Explicit-Root Result

Measured on 2026-10-10 in the isolated cache lane, using Python 3.14.3 on macOS
arm64 and Astichi's native Rust engine. The cache and opt-in Lifecycle adapter
are uncommitted. These measurements do not approve default activation or change
the active Pyrolyze integration lane.

This section records the initial opt-in implementation. The operator has since
authorized default-on automatic placement; the current benchmark explicitly uses
`off` for its disabled control and tests all placement modes. Historical numbers
below are preserved, not substituted for the new policy's measurements.

Five fresh-process repetitions per configuration and workload:

| Workload | Disabled median (min-max) | Empty cache median (min-max) | Populated cache median (min-max) | Warm speedup |
| --- | --- | --- | --- | --- |
| Normal context startup | 1.346 s (1.331-1.811) | 1.360 s (1.325-2.262) | 0.175 s (0.174-0.293) | 7.69x |
| Tk six-control startup | 1.781 s (1.538-2.184) | 2.021 s (1.930-2.492) | 0.256 s (0.242-0.517) | 6.96x |

Populated-cache startup saves 1.171 seconds (87.0%) on the normal context path
and 1.525 seconds (85.6%) on the Tk workload. Each disabled/empty-cache process
generates thirteen lifecycle implementations. Every populated-cache process has
thirteen hits, zero misses/bypasses, and zero generation calls. Warm probes reject
any generation attempt and confirm the lifecycle generator module stays unloaded.
Fresh execution and class construction still occur.

Including interpreter launch, benchmark-script imports, and process shutdown,
the corresponding parent-measured medians are:

| Workload | Disabled | Empty cache | Populated cache |
| --- | --- | --- | --- |
| Normal context startup | 1.483 s | 1.483 s | 0.255 s |
| Tk six-control startup | 1.923 s | 2.203 s | 0.370 s |

Both workloads use thirteen artifacts totaling 551,889 bytes (about 539 KiB).
Dependency setup inventories 136 files once per enabled process. The machine was
not otherwise quiesced; the ranges show substantial scheduling/load variation.
The cold cache has no demonstrated latency benefit and adds inventory, integrity,
serialization, dependency-recheck, and disk-write work. In particular, its Tk
median is about 0.24 seconds slower than disabled. Do not interpret overlapping
normal-context cold/disabled ranges as proof that miss overhead is negligible.

The old 1.02-second baseline in the shared plan is historical. The gains above
compare current disabled and enabled runs in this same checkout, not a current
warm run against that earlier measurement.

## Workloads And Boundaries

The benchmark is `tests/data/perf/benchmark_lifecycle_startup.py`.

- `context` imports the normal `pyrolyze.runtime.context` surface, with
  `PYROLYZE_CONTEXT_IMPL=lifecycle` pinned in each child process.
- `tk-six` then requests the real grouped `TkinterUiLibrary` members `CFrame`,
  `CLabel`, `CButton`, `CEntry`, `CCombobox`, and `CTtkButton`. This exercises
  compiler initialization and control-definition loading, matching the earlier
  six-control startup workload.
- Neither workload creates a GUI, runs a render, or measures time to a visible
  window. A full application's rendering/widget/event-loop performance is not
  established here.

An initial exploratory import of `pyrolyze.runtime.context_lcm` added eight
older compatibility-route classes, producing a twenty-one-class workload. Those
results are excluded from the accepted comparison above. The normal route
contains the thirteen intended classes, and each subprocess asserts its cache
counters and the driver verifies identical class lists across configurations.

For each workload the driver first primes ordinary Python bytecode/filesystem
caches and populates one private generated-code cache. Each disabled run has the
cache variable removed; every cold run gets a separate empty private directory;
each warm run shares the previously populated directory in a new process. Mode
order rotates across repetitions. Here, "cold" means an empty generated-code
cache, not a machine reboot or cleared OS page cache. Native selection is explicit
and verified on generating paths; the normal warm context path need not import
Astichi at all.

The child startup timer begins before the Lifecycle import and ends after the
workload. It includes cache setup, harvesting, fingerprinting, generation when
needed, compilation, cache I/O, module execution, and class binding. The parent
also reports complete subprocess wall time separately. Only generation/class
count wrappers run during the principal samples; detailed phase timing is a
separate process, and no cProfile/tracemalloc instrumentation affects the five
latency repetitions.

## Remaining Costs

The separate instrumented Tk probe gives these illustrative phase times. These
are single diagnostic samples, not medians or additive estimates for the main
latency table:

| Phase, summed over thirteen classes where applicable | Disabled | Empty cache | Populated cache |
| --- | --- | --- | --- |
| Lifecycle import/setup | 27.85 ms | 69.98 ms | 37.48 ms |
| Harvesting | 4.89 ms | 6.59 ms | 5.51 ms |
| AST generation | 1530.52 ms | 1524.83 ms | 0 |
| AST compilation | 47.85 ms | 49.90 ms | 0 |
| Lookup/producer boundary excluding generation and compilation | 4.76 ms | 181.23 ms | 30.11 ms |
| Generated module execution | 0.15 ms | 0.22 ms | 0.08 ms |
| Fresh class construction | 1.86 ms | 3.27 ms | 2.49 ms |
| Complete decorators | 1590.44 ms | 1766.73 ms | 38.48 ms |

Decorator totals contain the other decorator phases; do not add those rows again.
The lookup boundary combines fingerprinting, envelope/integrity checking,
deserialization, storage trust checks, and miss publication where applicable; it
is not pure disk-read time. With caching disabled it mostly measures producer
bookkeeping outside the AST/compile timers. Import/setup combines ordinary
imports with optional dependency inventory; it does not isolate inventory alone.

In the five uninstrumented Tk samples, import/setup medians were 36.68 ms
disabled, 49.21 ms cold, and 43.56 ms warm. On the normal context path they were
21.78 ms, 33.34 ms, and 32.73 ms respectively.

The expensive assembly/compilation work is removed on hits. Fresh class building
is already a small cost, so caching live classes would sacrifice correct rebinding
for little additional benefit. Further optimization would need to measure
fingerprinting/cache validation and one-time dependency setup, alongside remaining
Pyrolyze/compiler imports. This measurement does not justify weakening integrity
checks or changing invalidation policy.

## Reproduction

Run from this repository with the neighboring Pyrolyze checkout available. The
normal Lifecycle environment needs `frozendict` for the application probe; no Qt
or DearPyGui dependency is needed and no GUI is created:

```bash
uv sync --extra dev
uv pip install --python .venv/bin/python 'frozendict>=2,<3'
PYTHONPATH=src:../yidl-cache/src:../yidl/src:../astichi/src:../pyrolyze/src:../pyrolyze \
  .venv/bin/python tests/data/perf/benchmark_lifecycle_startup.py --repeats 5
```

Use `--workloads context` or `--workloads tk-six` for a single workload. The
interpreter must include tkinter for the Tk probe, and Astichi's native extension
must be built for it. The script fails rather than accepting Python fallback,
cache bypass, or an unexpected warm generation.

The current driver outputs one JSON object per placement and workload, including all repetitions, medians,
ranges, full subprocess times, generation/cache counters, class names, artifact
size, and separately instrumented phase probes. It copies Pyrolyze source and
creates a temporary home for each sample, primes ordinary Python bytecode outside
the timer, and blocks local cache storage for home-fallback probes. No real home
or active source-local generated cache is used. Temporary private caches are
removed afterward. Raw local output for this run is retained in ignored
`scratch/startup-cache-python314-public.jsonl`; the results above are the durable
record and the script reconstructs fresh evidence.

Revisions: Pyrolyze `1df84757a977d226869c4a091571d13b75b28fc6`, Astichi
`1c47f781d3804130fdd61cbee07a3b2e4529158a`, YIDL
`354c03cb96b57a320722f4a34e554f87237b9e6f`, and Lifecycle base
`c2502f1a7a565624f20cf930fde92f581b123e9f` plus the uncommitted cache adapter.
Shared cache version: uncommitted `0.1.0` implementation.

## Outstanding Gates

Implementation review, cross-platform trust/storage verification, and
commit/publication remain separate gates. Default-on implementation is now
operator-authorized; design approval is not implementation/release approval.
Existing canonical cache fixtures
cover fresh runtime binding and correctness; these startup measurements do not
replace that coverage or approve the active Pyrolyze LCM cleanup.

## Automatic Placement Evidence

The default-on policy driver was rerun on Python 3.14.3/macOS arm64/native.
Five fresh-process samples per cell; values are startup median (min-max), seconds.
Source copies, temporary home roots, explicit disabled controls, and generation-
forbidden warm processes separate placement effects from active-workspace state.

Initial implementation, pinned by `CacheLocationImplementationTuple.md` in the
neighboring cache repository:

| Placement | Workload | Disabled | Empty cache | Populated cache | Speedup |
| --- | --- | --- | --- | --- | --- |
| Override | Context | 1.938 (1.501-2.711) | 2.501 (1.721-2.805) | 0.251 (0.206-0.414) | 7.74x |
| Override | Tk six | 2.750 (2.027-3.129) | 2.643 (1.989-3.317) | 0.427 (0.308-0.669) | 6.44x |
| Local | Context | 2.877 (2.245-3.297) | 3.084 (2.920-3.353) | 0.419 (0.367-0.467) | 6.87x |
| Local | Tk six | 3.054 (2.926-3.202) | 3.128 (2.848-3.458) | 0.518 (0.452-0.558) | 5.89x |
| Home fallback | Context | 2.847 (2.657-3.088) | 2.952 (2.781-3.460) | 0.456 (0.405-0.511) | 6.24x |
| Home fallback | Tk six | 2.868 (2.836-3.181) | 3.103 (2.876-3.202) | 0.506 (0.489-0.652) | 5.67x |

After bounded code/state corrections (tuple `CacheLocationImplementationTuple-2.md`),
the two automatic routes were repeated for the normal thirteen-class context:

| Placement | Disabled | Empty cache | Populated cache | Speedup |
| --- | --- | --- | --- | --- |
| Local | 2.552 (2.443-3.027) | 2.700 (2.532-3.029) | 0.426 (0.392-0.492) | 5.99x |
| Home fallback | 2.738 (2.488-3.898) | 3.032 (2.842-3.223) | 0.497 (0.410-0.716) | 5.51x |

Every populated-cache process reported thirteen hits, zero misses/bypasses, and
zero generation. The initial placements each stored thirteen artifacts totaling
551,889 bytes, and automatic probes assert the selected layout type. Home tests
block local storage with a regular file; no real source/home permissions change.

The workstation had concurrent load. Do not compare absolute times across this
table, the corrected rerun, or the historical baseline as controlled regressions.
Within each rotated comparison the advantage is substantial; empty caches still
pay for generation and storage. The corrected cold medians add roughly 0.15/0.29
seconds over disabled. These results do not justify weaker trust checks or live
class caching.

Reproduce the corrected bounded measurement from this repository:

```bash
PYTHONPATH=src:../yidl-cache/src:../yidl/src:../astichi/src:../pyrolyze/src:../pyrolyze \
  .venv/bin/python tests/data/perf/benchmark_lifecycle_startup.py \
  --repeats 5 --workloads context --placements local home
```

Raw output is retained in ignored `scratch/location-startup-python314.jsonl` and
`scratch/location-startup-python314-corrected.jsonl`. Performance evidence does
not close code/state findings or authorize commit/publication.
