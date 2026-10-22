# Lifecycle Compiled Code Cache

## Boundary

The default-on adapter is implemented in `src/yidl_lifecycle/lifecycle_code_cache.py`.
`lifecycle_cache_configuration.py` owns startup settings and bounded source origins.
`lifecycle_cache_inputs.py` owns the explicit generation-input schema. The shared
artifact package remains independent; YIDL core does not import or depend on it.

Lookup occurs after harvesting and before `_generate_lifecycle_ast`. A miss
still assembles the executable AST and compiles it directly, without source
round-tripping. A normal hit skips assembly and compilation. A hit reached after
local publication failure can already have generated code; diagnostics record
that distinction. Both paths execute module
code in a fresh namespace and call the builder with the current harvested
arguments and decorated class. The cache never retains live classes or instances.

Generation, compilation/execution, and builder errors preserve the existing
class-context diagnostics. Definition validation runs on every decoration;
invalid factory dependencies cannot create successful cache entries. Counter
hits and misses describe compiled-code reuse, not successful class binding.

## Configuration And Relative Dependencies

Local development resolves the sibling package through this repository's
`pyproject.toml`:

```toml
[tool.uv.sources]
yidl-cache = { path = "../yidl-cache", editable = true }
```

Distribution metadata requires `yidl-cache>=0.1.0`. Checkout paths do not leak
into wheel requirements. Reinstall editable registrations after copying an
environment; relative source declarations alone do not relocate copied launchers
or editable-install registrations.

Settings are captured before the first Lifecycle import:

| Setting | Meaning |
| --- | --- |
| `YIDL_LIFECYCLE_CACHE` unset/empty or `on` | Enable automatic compiled-code reuse (default). |
| `YIDL_LIFECYCLE_CACHE=off` | Disable caching, dependency inventory, and cache directory creation; wins over any directory override. |
| Other nonempty enable value | Disable safely, with a typed configuration diagnostic. |
| `YIDL_LIFECYCLE_CACHE_DIR` unset/empty | Use automatic local storage, then private home fallback. |
| Nonempty directory override | Use only this root; unusable override bypasses, not home fallback. |

Enable values ignore case and surrounding whitespace. Directory whitespace is
literal. Relative roots are normalized against the startup working directory,
not a later directory change. Current-user `~`/`~/` expands; `~other` is rejected,
and `$VARIABLES` are not expanded. Cache roots are not resolved through symlinks.
Python's `-B`, `PYTHONDONTWRITEBYTECODE`, and `sys.pycache_prefix` do not control
these custom artifacts; use the explicit off switch instead.

For a regular loaded `.py`/`.pyw` module, origin discovery uses already-loaded
`__spec__.origin`, then `__file__`. The author-file symlink is resolved, without
reading source. At most 32 origin decisions are retained, without module/class
references. Unknown, interactive, frozen, or archive origins use the home route.

Automatic locations are:

```text
<source-parent>/__pycache__/yidl_cache/ns-<namespace-digest>/<identity>.ycode
~/.yidl/cache/ns-<namespace-digest>/sources/<volume>/<source-path>/module.py/<identity>.ycode
~/.yidl/cache/ns-<namespace-digest>/modules/<module-name-digest>/<identity>.ycode
```

Every namespace is encoded as a digest of its exact UTF-8 bytes, preventing
case-insensitive and literal/hash-directory aliasing. Source components are
encoded independently; oversized components/paths use `sources/by-digest/`
instead. An override uses `<override-root>/ns-<namespace-digest>/` and leaves
old flat-root prototype entries untouched. `.ycode` is a versioned integrity
envelope, not a CPython `.pyc` file.

Admission verifies private writable storage with an exclusive create/remove
probe. Unsafe local storage falls back to home; unavailable home falls back to
normal generation. Private leaves use `0700` and files `0600`. Existing unsafe
permissions are never repaired. All operations retain descriptor-based symlink,
ownership, ACL, file-size, format, and integrity checks. A selected fallback is
preferred while its route is tracked, without skipping subsequent trust checks.
Producer exceptions never trigger fallback or duplicate generation. One shared
code LRU/invalidation/reentry state spans every route.

```bash
YIDL_LIFECYCLE_CACHE_DIR=scratch/lifecycle-code-cache uv run python your_app.py
YIDL_LIFECYCLE_CACHE=off uv run python your_app.py
```

Configuration and producer provenance remain fixed for the process. Restart
after configuration changes, generator edits, or engine-selection changes.

## Fingerprints And Invalidation

The fingerprint includes the complete supported class/field/method fact schemas,
ordered fields and methods, factory provider names, annotation text, slot names,
comparison/mutability/conversion flags, builder parameter names, and transaction
topology. Actual key objects are projected into harvested indexes, including
default-key membership. Explicit method indexes and ordered field assignments
retain both harvested and generated grouping inputs. Astichi environment
settings are included without importing its engine.

Actual defaults, factory/converter objects, resource objects, and user methods
are rebound at runtime. They are not serialized or hashed using repr. Only
exact string field annotations are initially cacheable; live annotations,
unknown schemas, unsupported literal shapes, and oversized definitions take
the ordinary generation path. Typed encodings distinguish booleans, integers,
strings, tuples, and None.

The adapter inventories source files in Lifecycle, YIDL, and Astichi, plus
installed/package-local native extensions and Astichi's editable native-engine
directory. It enumerates and stats them once before deferred generator loading.
The shared cache rechecks inventory only before publishing a miss. Warm hits do
not scan dependencies or import templates.

Dependency identity uses modification timestamps and sizes, not content hashes.
Ordinary fresh-process edits invalidate entries. An observed edit during a miss
suppresses publication and disables that producer for the process. Automatic hot
reload is unsupported. Edits preserving timestamps and sizes, or edit/restore
races invisible between checks, are accepted limitations. Clear and restart
after such edits; clearing alone does not remove a process invalidation fence.

## Diagnostics And Clearing

```python
from yidl_lifecycle.lifecycle_code_cache import (
    cache_configuration, cache_diagnostics, cache_statistics, clear_code_cache,
)

settings = cache_configuration()  # Frozen startup decision, including config problem.
statistics = cache_statistics()  # None when disabled; otherwise frozen counters.
decisions = cache_diagnostics()   # Up to 32 frozen snapshots, oldest first.
removed = clear_code_cache()    # Explicit artifact cleanup, not a request-path scan.
```

No automatic logging occurs. A decision records the selected/attempted typed
locations, final outcome type, generation flag, and bounded typed failure and
artifact-rejection summaries. Repeated requests each get a snapshot; no exception
objects, tracebacks, or live code/classes are retained in diagnostics.

With an explicit root, clearing targets its consumer namespace even before the
first decoration. Automatic clearing targets only candidates in the currently
tracked 32 routes, including
recognized artifacts, temporary writes, and admission probes. It does not crawl
all module/home cache directories or remove another namespace. Memory,
preferences, and diagnostic history are cleared even on maintenance failure;
producer invalidation fences survive. Evicted/untracked directories and legacy
flat-root artifacts remain. Statistics are cumulative.

Disabling does not delete existing artifacts: with `off`, `clear_code_cache()`
returns zero and performs no maintenance. Clear while enabled before disabling,
or use an enabled maintenance-only process for an explicit root:

```bash
YIDL_LIFECYCLE_CACHE=on YIDL_LIFECYCLE_CACHE_DIR=scratch/lifecycle-code-cache \
  uv run python -c 'from yidl_lifecycle.lifecycle_code_cache import clear_code_cache; print(clear_code_cache())'
YIDL_LIFECYCLE_CACHE=off uv run python your_app.py
```

An automatic cache still requires the relevant routes to be tracked in that
process; this command does not discover or clear untracked module/home caches.
Set `YIDL_LIFECYCLE_CACHE=off` and restart to disable. Shared
cache trust supports macOS/Linux inspection and Windows fixed-local-NTFS
ownership/ACL and handle checks. Windows ReFS and other unsupported storage
routes bypass; a source on ReFS can still use the automatic NTFS home fallback.
See the [Windows policy and verification amendment](../../yidl-cache/dev-docs/WindowsPersistence.md)
for exact guarantees and qualification limits. Cross-platform release approval
remains separate.

## Verification

The canonical fixture is `tests/data/cache/lifecycle_process.py`. It covers
parent/child inheritance, current runtime defaults, named factories, freeze/thaw,
retained initvars for transient reevaluation, lazy mutable and local storage,
bindings/owned values, hooks, object-valued transaction keys, commit, and rollback.

```bash
YIDL_LIFECYCLE_CACHE_DIR=scratch/lifecycle-proof uv run python tests/data/cache/lifecycle_process.py 10 no
YIDL_LIFECYCLE_CACHE_DIR=scratch/lifecycle-proof uv run python tests/data/cache/lifecycle_process.py 90 yes
```

Use a new proof directory for the first command when checking cold counts. The
cold process generates two builders. The next process hits both and binds its
new value. Warm assertions forbid assembly, AST compilation, and dependency
rechecks, and verify the generated base, Astichi, and YIDL assembly runtime were
not imported.

Run the focused adapter and fingerprint checks:

```bash
YIDL_LIFECYCLE_CACHE=off uv run python -m pytest -q tests/test_lifecycle_code_cache.py tests/test_cache_configuration.py
```

The original opt-in adapter passed both engines, targeted Python 3.12 through
3.15 alpha checks, and 408 full-suite tests with 46 skips on Python 3.14.
Automatic-placement verification is recorded separately in the
[location checkpoint](../../yidl-cache/dev-docs/CacheLocationPolicyCheckpoint.md),
including explicit, local, and home fresh-process reuse. Existing generated
goldens remain unchanged.

Lifecycle and cache wheels were installed into a fresh environment, with YIDL
and Astichi resolved explicitly from the lane's sibling sources. The fixture
passed cold and generation-forbidden warm runs with isolated-interpreter mode.
Both Lifecycle and cache imports resolved from installed wheels; wheel metadata
declares the named cache requirement without a checkout path.

The implementation is uncommitted and enabled by default. These are local
macOS results, not Linux/Windows release approval.

## Startup Measurement

The historical opt-in explicit-root probe fell from 1.346 to 0.175 seconds for
the thirteen-class context path, and from 1.781 to 0.256 seconds for Tk startup.
The corrected automatic-placement probe, with five fresh-process samples per
configuration, fell from 2.552 to 0.426 seconds locally and from 2.738 to 0.497
seconds through home fallback. Every warm process has thirteen hits and zero
generation. Cold generation still incurs setup/storage work. Absolute times
across runs reflect concurrent workstation load, not a controlled regression.

See [startup measurements](LifecycleCodeCacheStartup.md) for the full ranges,
phase timings, cache size, exact boundaries, reproduction, and current revisions.
These are local Python 3.14/macOS startup measurements without GUI creation;
they are not measurements of rendering or a whole visible application.

## Remaining Gates

Code/state and sequential user-surface review accepted the content-pinned draft.
Two nonblocking documentation follow-ups clarify disabled maintenance and show
a complete shared-consumer example. Settled-tree acceptance, cross-platform
storage/trust approval, commits, publication,
and any integration with the active Pyrolyze cleanup remain outside this
checkpoint. The startup proof does not replace correctness or application-level
rendering/resource verification. The proposed Pyrolyze home YAML preferences are
a separate application-bootstrap facility; this adapter does not read them.
