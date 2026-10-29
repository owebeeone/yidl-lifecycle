# yidl-lifecycle

> **Full documentation:** [User guides and API reference](https://owebeeone.github.io/yidl-lifecycle/).

Try changes to your Python model, then keep them or discard them together.
Lifecycle lets you declare which fields participate in a transaction and read
both committed and pending values while editing. You write ordinary Python
classes; you do not need to write YIDL.

```sh
python -m pip install yidl-lifecycle
```

```python
from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Settings:
    volume: int = managed(default=5)


manager = TransactionManager()
settings = Settings(transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    settings.volume = 8
    assert settings.current.volume == 5  # Committed value is still visible.
    assert settings.working.volume == 8

assert settings.volume == 8  # Normal exit commits.
```

An exception inside the scope rolls back its pending managed values. Managed
assignment outside a transaction raises. Ordinary fields and external side
effects are not rolled back; views are live, not historical snapshots.

## Learn and use Lifecycle

Read the [documentation website](https://owebeeone.github.io/yidl-lifecycle/),
or follow the repository links below.

- [Start here](docs/GettingStarted.md): install, commit an edit and cancel one.
- [Understand the model](docs/Concepts.md): fields, transactions and live views.
- [Choose fields](docs/Markers.md): complete marker options and behavior.
- [Edit collections](docs/Collections.md): editable lists and committed tuples.
- [Coordinate objects and keys](docs/Transactions.md): shared edits and nesting.
- [Initialize dependent values](docs/Initialization.md): factories and lazy fields.
- [Validate and react to edits](docs/Hooks.md): validators and completion hooks.
- [Manage resources and failures](docs/Resources.md): ownership and recovery.
- [Transaction API](docs/TransactionReference.md) and
  [troubleshooting](docs/Troubleshooting.md): direct lookup and corrective actions.
- [Documentation index](docs/index.md): all guides and advanced references.

Lifecycle manages an edit in memory; it is not a database or an undo history.
Use it when selected model fields need a controlled commit/rollback boundary.
It does not provide thread/task isolation or undo arbitrary effects of user code.

## Compatibility and contributors

Version 0.1.1 is published on PyPI. The qualified CPython matrix is 3.12–3.15
with Astichi's Python backend; see [installation and support](docs/GettingStarted.md#install).
Dependencies are installed automatically. Licensed under LGPL-2.1-only.

For compiler architecture, generated builders, development commands and release
policy, see [contributing and internals](dev-docs/ContributorGuide.md). Existing
design, review and experiment records remain in [developer documentation](dev-docs/README.md).
