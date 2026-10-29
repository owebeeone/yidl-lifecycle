# Coordinate objects and transaction keys

A manager can complete changes to several objects under the same key. Use that
when one operation updates related model values. Read the [first transaction](GettingStarted.md)
and [view model](Concepts.md) first.

## Edit related objects together

This complete example transfers an in-memory quantity:

```python
from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Stock:
    quantity: int = managed(default=0)


manager = TransactionManager()
source = Stock(quantity=10, transaction_manager=manager)
destination = Stock(quantity=2, transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    source.quantity -= 3
    destination.quantity += 3
    assert (source.current.quantity, destination.current.quantity) == (10, 2)

print(source.quantity, destination.quantity)
```

It prints `7 5`. The same manager and key coordinate the edited participants.
An exception in this body would discard both pending scalar changes.

Objects may reference each other or be arranged in a tree, but the manager does
not automatically deep-copy that tree. Set up the same manager on each object
whose managed edits should participate. Plain mutable payloads and objects using
another manager are outside this boundary.

## Finish explicitly

For an application that starts and finishes an edit in different callbacks,
use the manager directly. This is a continuation of the example above:

```python
transaction = manager.begin(DEFAULT_TRANSACTION)
source.quantity = 6
manager.rollback(DEFAULT_TRANSACTION)
assert source.quantity == 7

transaction = manager.begin(DEFAULT_TRANSACTION)
source.quantity = 6
manager.commit(DEFAULT_TRANSACTION)
assert source.quantity == 6
```

The caller must eventually complete every begin. Prefer `with` when the edit
fits one scope. Avoid manually completing a transaction inside its `with`
scope: the scope still owns completion and will attempt to finish on exit.

## Nested scopes join an edit

This continuation demonstrates a successful joined edit:

```python
with manager.begin(DEFAULT_TRANSACTION):
    source.quantity = 4
    with manager.begin(DEFAULT_TRANSACTION):
        destination.quantity = 7
    assert source.current.quantity == 6  # Inner exit has not published.
assert (source.quantity, destination.quantity) == (4, 7)
```

Inner success closes one begin level; the outermost completion publishes.
An inner rollback aborts the joined transaction for that key. It is not a
savepoint. Do not catch an inner abort and continue as though the outer edit
were still active.

## Use a separate key only for a separate edit boundary

Define and register the key before using it:

```python
from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager

AUDIT = "audit"


@lifecycle
class Record:
    value: int = managed(default=0)
    audit_count: int = managed(AUDIT, default=0)


manager = TransactionManager(tx_keys=(AUDIT,))
record = Record(transaction_manager=manager)
with manager.begin(AUDIT):
    record.audit_count = 1
assert record.value == 0
assert record.audit_count == 1
```

Use explicit keys to make the intended boundary clear. Omitting keys on
manager operations selects the default key **and all configured custom keys**.
Several keys still complete independently; this is not an atomic multi-key
transaction. Completion of one key can succeed while another fails.

Access to a shared manager and model state must be serialized by the application.
There is no thread-local or async-task isolation. An `await` inside an edit does
not grant another task an independent transaction on that manager.

See the [transaction reference](TransactionReference.md) for signatures, return
values and errors. The [executable coordination example](../examples/transactions.py)
also checks an inner abort and independent custom-key changes.
