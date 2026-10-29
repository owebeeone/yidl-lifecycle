# Your first Lifecycle transaction

Suppose a user changes several settings and then chooses whether to keep them.
Lifecycle gives selected fields a committed value and a pending value, so you
can try an edit before publishing it to the rest of your model.

You need Python classes, decorators and `with` statements. You do not need to
learn YIDL or a code-generation API.

## Install

Use CPython 3.12–3.15 for the tested release matrix. In a virtual environment:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install yidl-lifecycle
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead of
the second line. Version 0.1.1 is published; dependencies install automatically.
No sibling checkouts or generation step are required.

The release qualification uses Astichi's Python backend. Select it before
starting Python:

```sh
export ASTICHI_LOWER_ENGINE=python
```

In PowerShell: `$env:ASTICHI_LOWER_ENGINE = "python"`. This controls code
generation, not your model's transaction behavior. Compiled-code caching remains
available. Windows Python 3.15 does not have a qualified Astichi 1.1.3 binary
wheel; a source build on that combination has not been qualified. The Python
version matrix is not a claim that every platform/backend combination works.

## Keep an edit

Save this complete example as `settings.py`:

```python
from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Settings:
    volume: int = managed(default=5)
    brightness: int = managed(default=50)


manager = TransactionManager()
settings = Settings(transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    settings.volume = 8
    settings.brightness = 70
    print("during:", settings.current.volume, settings.working.volume)

print("committed:", settings.volume, settings.brightness)

try:
    with manager.begin(DEFAULT_TRANSACTION):
        settings.volume = 2
        settings.brightness = 10
        raise ValueError("cancel this edit")
except ValueError:
    pass

print("after cancel:", settings.volume, settings.brightness)
```

Run `python settings.py`. Expected output:

```text
during: 5 8
committed: 8 70
after cancel: 8 70
```

`managed` marks the two fields as transactional. `manager` controls when editing
begins and ends. Inside `begin`, assignment updates pending values; normal
scope exit commits them. An exception rolls them back. The second edit therefore
leaves both fields at the values published by the first edit.

`.current` reads the committed value even while a change is pending. `.working`
reads the pending value. Ordinary `settings.volume` access also sees pending
values during an edit. These are views of one state, not copies.

## Reject an accidental edit

Add this continuation to the same file:

```python
try:
    settings.volume = 3
except RuntimeError:
    print("start a transaction before editing")
```

There is no active transaction, so the assignment raises and the value remains
8. Construction is allowed to supply initial managed values; later edits need
the matching transaction.

## Check your understanding

If the first edit set `volume` to 9 instead, what would `after cancel` print?
Answer: `9 70`. Rollback discards the second edit; it does not restore the
original construction values or undo an earlier commit.

The executable [settings example](../examples/settings.py) also demonstrates
explicit manager-owned commit and rollback outside a `with` statement.

Next, [understand fields and live views](Concepts.md). For a specific task, use
the [guide index](index.md) directly.
