# yidl-lifecycle

Lifecycle decorator and transactional lifecycle runtime built on YIDL.

This repository is being split out of `yidl` so lifecycle can act as a real
downstream compiler package while `yidl` stays focused on the generic compiler
substrate.

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

See [cache integration](dev-docs/LifecycleCodeCache.md) for supported fingerprints,
invalidation caveats, diagnostics, clearing, and the fresh-process proof.

## Development

From this repository root:

```bash
PYTHONPATH=../astichi/src uv run --with pytest python -m pytest -q
```

The project is expected to use the sibling `../yidl` checkout during local
development.
