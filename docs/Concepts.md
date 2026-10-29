# Fields, transactions and live views

Start with [a working transaction](GettingStarted.md). Here we explain which
values an edit changes and what you see while it is in progress.

## One edit boundary, selected fields

A **managed field** has a committed value and, during a transaction, a pending
working value. A **transaction manager** coordinates the objects participating
in an edit. A **transaction key** selects a group of fields; the ordinary case
uses `DEFAULT_TRANSACTION`.

Beginning a transaction opens editing. Commit publishes pending managed values;
rollback discards them. Construction establishes initial values without an
active edit. This is in-memory state management, not database persistence.

An ordinary `field` updates immediately. It is useful for information that
should survive an abandoned edit, but it must not be chosen for data you expect
rollback to restore.

## Three ways to read the same state

| Access | Managed scalar reads | Managed assignment |
| --- | --- | --- |
| `model` or `model.default` | Pending value when present, otherwise committed | Requires its active transaction |
| `model.current` | Committed value | Rejected |
| `model.working` | Pending value with committed fallback | Requires its active transaction |

For collections, `.working` also requests the editable representation; an
ordinary read does not initiate thawing. See [editing collections](Collections.md).

For the first tutorial's volume:

| Moment | `settings.volume` | `settings.current.volume` | `settings.working.volume` |
| --- | --- | --- | --- |
| Constructed | 5 | 5 | 5 |
| Pending assignment to 8 | 8 | 5 | 8 |
| After commit | 8 | 8 | 8 |
| Pending assignment to 2 | 2 | 8 | 2 |
| After rollback | 8 | 8 | 8 |

These access objects are called **facades** in the API. They are live views,
not snapshots. Keeping `saved = settings.current` does not preserve today's
values: after the next successful edit, `saved.volume` reads the new committed
value too. Copy the values you need if you want an independent application
snapshot; Lifecycle does not retain an undo history.

## A revealing contrast

This standalone example intentionally mixes managed and ordinary storage:

```python
from yidl_lifecycle.lifecycle import field, lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Counter:
    count: int = managed(default=0)
    last_attempt: str = field(default="none")


manager = TransactionManager()
counter = Counter(transaction_manager=manager)
saved_view = counter.current

try:
    with manager.begin(DEFAULT_TRANSACTION):
        counter.count = 4
        counter.last_attempt = "changed count"
        raise ValueError("cancel")
except ValueError:
    pass

print(counter.count, counter.last_attempt)
with manager.begin(DEFAULT_TRANSACTION):
    counter.count = 7
print(saved_view.count)
```

It prints `0 changed count`, then `7`. Before running it, try to explain both
results: rollback only restores the managed count, and the saved view remains
live. This distinction also applies to nontransactional constants, lazy values
and local scratch storage.

## Boundaries to remember

- Read-only access to managed fields does not make every object reachable from
  the facade immutable. `const` protects a reference from replacement; mutable
  contents still need their own policy.
- User methods run through the views too. Calling a method through `.current`
  can still change ordinary fields or perform external side effects.
- Related objects participate by sharing a manager/key and being enlisted as
  edited. A transaction is not an automatic recursive snapshot of an object tree.
- Nested scopes on one key join; they are not savepoints. Managers do not supply
  concurrent thread/task isolation. See [transaction boundaries](Transactions.md).

Choose a policy using the [field reference](Markers.md), or continue with
[collections](Collections.md).
