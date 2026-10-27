# yidl-lifecycle

Lifecycle decorator and transactional lifecycle runtime built on YIDL.

This standalone package owns the decorator and transaction behavior; YIDL owns
the generic compiler. The 0.1.1 compatibility patch pins Astichi 1.1.3, YIDL 0.1.2 and
Cache 0.1.0, plus compat-sentinel 0.1.2. The declared test matrix covers
CPython 3.12–3.15. See [release preparation](RELEASE.md) for
the publication order and verification boundary. Licensed under LGPL-2.1-only.

## Start here

Read [installation and your first transaction](docs/GettingStarted.md), then use
[fields and hooks](docs/Markers.md), [transactions and views](docs/ManagedContextApiDraft.md)
and [cache troubleshooting](docs/Cache.md) for the task at hand. The initial
0.1.0 release is on PyPI; the 0.1.1 patch qualifies the updated compiler pin
and Python 3.15.

## Generated Builders And Runtime Dependencies

Lifecycle ships a committed generated base in its wheel and source distribution;
installation does not regenerate it. The public `lifecycle` decorator is a
handwritten entry point that uses this base to build each decorated class.

YIDL is a runtime dependency as well as the compiler used for regeneration.
The generated base imports YIDL's record/container primitives, assembly-plan
objects, assembly execution engine, and Astichi template adapters. Lifecycle's
field markers use its own module-owned sentinels from the published
`compat-sentinel` package. A normal generation-free cache hit avoids assembly
and compilation, but does not make Lifecycle independent of YIDL.

**Lifecycle must pin the exact published YIDL version used to regenerate and
qualify its shipped builders.** It must not declare an open-ended minimum YIDL
version or derive the pin from an arbitrary developer environment. Supporting
a different YIDL release requires regeneration, compatibility checks, and a
Lifecycle release with the corresponding exact dependency pin. See the
[release process](RELEASE.md#yidl-compatibility-contract).

Astichi supplies the template/composition runtime used through YIDL. Its
compatibility also needs qualification; it is not automatically interchangeable.
The current release pins Astichi too. A wider Astichi range would need separate
validation and consistent dependency declarations in both YIDL and Lifecycle.

## Lazy Fields

`lazy` declares per-instance, non-transactional, write-once storage. An explicit
constructor value or first assignment initializes it; otherwise its first read
uses the declared default or calls the default factory. Factory providers are
read at that first access, not during construction. Later assignments raise by
default; `mutable=True` permits immediate replacement through any facade. The
stored object's contents are not recursively frozen.

```python
from yidl_lifecycle.lifecycle import lazy, lifecycle


@lifecycle
class Config:
    items: list[int] = lazy(default_factory=list)
    cache: dict[str, int] = lazy(default_factory=dict, mutable=True)
```

`static` remains an exact compatibility alias. Both names retain the existing
internal `static` field kind and generated diagnostics. Assigning before first
read bypasses the factory; replacement does not rerun it. Neither policy adds
transaction participation, invalidation, or automatic recomputation.

## Generated Code Cache

Compiled Lifecycle builders can be reused across processes through the standalone
`yidl-cache` package. Caching is on by default on supported platforms. The adapter
tries the declaring module's `__pycache__/yidl_cache/ns-<namespace-digest>` first,
then a private mirrored source directory under `~/.yidl/cache`. Unsafe or unwritable
locations fall through to normal generation, not an import failure.

Set controls before importing the decorator:

```bash
YIDL_LIFECYCLE_CACHE=off uv run python your_app.py
# Or force one private root (no automatic fallback when this root is unusable):
YIDL_LIFECYCLE_CACHE_DIR=scratch/lifecycle-code-cache uv run python your_app.py
```

An explicit `off` wins over the directory override. Settings are captured once;
restart after changes. Python's `-B`/`PYTHONDONTWRITEBYTECODE` and `pycache_prefix`
do not control this cache. Missing directories are created privately; unsafe or unavailable storage falls
back to normal generation. Each decoration still harvests and validates the
definition, executes code in a fresh namespace, and binds current defaults,
factories, converters, transaction keys, and the user class. Only assembly and
AST compilation are skipped on a generation-free hit. A final home hit after
failed local publication may already have generated; `cache_diagnostics()`
reports that distinction. Disabling retains existing artifacts; clear while
enabled if removal is required. Clearing while disabled is a no-op.

Local development uses the relative sibling source `../yidl-cache`, configured
in `tool.uv.sources`. Published package metadata uses the named distribution
dependency, not a checkout path.

See [cache controls and troubleshooting](docs/Cache.md) for normal use. The
[integration record](dev-docs/LifecycleCodeCache.md) contains detailed fingerprints
and the fresh-process proof.

## Development

From this repository root:

```bash
PYTHONPATH=../astichi/src uv run --with pytest python -m pytest -q
```

The project is expected to use the sibling `../yidl` checkout during local
development.
