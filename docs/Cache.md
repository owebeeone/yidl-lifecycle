# Configure and diagnose caching

Caching reuses compiled class-builder code. It does not store live classes,
instances, defaults or callbacks. Every decoration still harvests the class,
executes code in a fresh namespace and binds the current runtime objects.

## Controls

Set these before the first Lifecycle import and restart after changes:

| Environment setting | Result |
| --- | --- |
| `YIDL_LIFECYCLE_CACHE` unset, empty or `on` | Automatic caching on supported storage |
| `YIDL_LIFECYCLE_CACHE=off` | Disable caching and cache-directory creation |
| `YIDL_LIFECYCLE_CACHE_DIR=...` | Use one explicit root; no automatic fallback if it is unusable |

`off` takes precedence over a directory override. A relative root is anchored to
the startup working directory. On Unix shells, for example:

```sh
YIDL_LIFECYCLE_CACHE=off python counter.py
```

In PowerShell, set `$env:YIDL_LIFECYCLE_CACHE = "off"` before `python counter.py`.
Python's bytecode switch `-B` does not disable this separate cache.

Automatic placement tries the declaring module's `__pycache__/yidl_cache` route,
then private storage under `~/.yidl/cache`. Unknown/interactive origins use the
home route. Unsupported or unsafe storage leads to ordinary generation.
Mac/Linux paths must satisfy private ownership/permission/ACL checks; symlinked
cache paths are not accepted. Windows persistence requires trusted fixed local
NTFS; unsupported volumes can use a valid automatic NTFS home fallback.

## Inspect or clear

```python
from yidl_lifecycle.lifecycle_code_cache import (
    cache_configuration,
    cache_diagnostics,
    cache_statistics,
    clear_code_cache,
)

print(cache_configuration())
print(cache_statistics())
for decision in cache_diagnostics():
    print(decision)
removed = clear_code_cache()
print("removed", removed)
```

Clearing is an explicit maintenance operation. It visits the configured root or
currently tracked automatic routes, not every cache on disk. It does not delete
unrelated files or reset a producer invalidation fence. With caching disabled,
clearing does nothing: clear while enabled before disabling if removal is needed.

## Troubleshooting

| Symptom | Check and action |
| --- | --- |
| No hit for a class | Only supported input shapes are cacheable; live annotation objects can bypass. Ordinary generation is a valid result. |
| Always generating with an explicit directory | Inspect configuration and location failures. Use a canonical private path with supported ownership/permissions; do not broaden permissions or expect automatic fallback. |
| Hit counter increased but startup still generated code | A fallback hit can follow failed local publication after generation. Inspect the diagnostic's `generated` flag. |
| Edits are not reflected in a running process | Hot reload is unsupported. Restart after generator/configuration changes. |
| Clearing removed fewer entries than expected | Maintenance is bounded to tracked routes; disabled caching and evicted/untracked routes are not a recursive cleanup service. |
| Import or class construction fails | Producer/build errors propagate. Disabling persistence is a diagnostic comparison, not a fix for an invalid class definition or incompatible dependency tuple. |

Invalidation uses captured dependency timestamps and sizes. Preserving both can
hide edits; clear and restart when necessary. This is not a sandbox for hostile
code or a content-hash guarantee. The [integration record](../dev-docs/LifecycleCodeCache.md)
and [Cache policy](https://github.com/owebeeone/yidl-cache/blob/main/docs/CachePolicy.md)
explain the complete limits and diagnostics.
