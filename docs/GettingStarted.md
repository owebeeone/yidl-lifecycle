# Start with Lifecycle

Lifecycle turns a Python class into an object with declared field policies and
transaction-aware views. You write the class and apply `@lifecycle`; you do not
need to author YIDL source for ordinary use.

## Install

Use CPython 3.12 or newer. The current release checks cover the explicit Python
backend on Python 3.12, 3.13 and 3.14; other backends/platforms need their own
evidence. The first release is being prepared: the registry command below is
for use **after publication**, not a claim that the package is already on PyPI.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install 'yidl-lifecycle==0.1.0'
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead of the
second line. Installation obtains the pinned YIDL, Cache, Astichi and
compat-sentinel dependencies automatically. You do not need sibling checkouts.
For pre-publication verification, put the approved candidate wheels in
`candidate/` and install them together:

```sh
python -m pip install candidate/yidl_cache-0.1.0-py3-none-any.whl candidate/yidl-0.1.0-py3-none-any.whl candidate/yidl_lifecycle-0.1.0-py3-none-any.whl
```

Select the qualified backend before starting Python:

```sh
export ASTICHI_LOWER_ENGINE=python
```

In PowerShell, use `$env:ASTICHI_LOWER_ENGINE = "python"`. This selects Astichi's
Python code-generation backend; it does not disable Lifecycle's compiled-code
cache. See [cache controls and troubleshooting](Cache.md).

## Make and edit a counter

Save this as `counter.py`:

```python
from __future__ import annotations

from yidl_lifecycle.lifecycle import field, lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Counter:
    count: int = managed(default=0)
    label: str = field(default="counter")


manager = TransactionManager()
counter = Counter(transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    counter.count = 1
    assert counter.working.count == 1
    assert counter.current.count == 0

assert counter.current.count == 1

try:
    with manager.begin(DEFAULT_TRANSACTION):
        counter.count = 2
        counter.label = "attempted edit"
        raise ValueError("cancel")
except ValueError:
    pass

assert counter.count == 1
assert counter.label == "attempted edit"
print(counter.current.count, counter.label)
```

Run `python counter.py`. It prints `1 attempted edit`. Normal scope exit commits
the managed count; the exception aborts its next change. The plain label updates
immediately and is not rolled back. Assigning the managed count outside its
active transaction raises.

The ordinary object and `.default` are overlay-aware. `.current` reads committed
managed values; `.working` exposes pending values with committed fallback.
These are live views of the same state, not copies or historical snapshots.

## Choose the next task

- Choose storage: [field and hook reference](Markers.md).
- Use custom keys, shared managers or aggregates: [transactions and views](ManagedContextApiDraft.md).
- Understand reference lifetimes: [facade ownership](FacadeOwnership.md).
- Configure, diagnose or clear caching: [compiled-code cache](Cache.md).
- Prepare a compatible package: [release process](../RELEASE.md).
