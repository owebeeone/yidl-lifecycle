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

## Development

From this repository root:

```bash
PYTHONPATH=../astichi/src uv run --with pytest python -m pytest -q
```

The project is expected to use the sibling `../yidl` checkout during local
development.
