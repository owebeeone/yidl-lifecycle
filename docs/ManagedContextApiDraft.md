# ManagedContext: Transaction-Scoped Editing

Status: user-facing DRAFT, 2026-10-03. Existing API is shown first. Proposed
constructor aliases and static changes at the end are not implemented yet.

Pyrolyze calls the decorator `managed_context`. The library calls it
`lifecycle`; they are the same decorator, not two implementations.

## Edit And Complete A Transaction

```python
from yidl_lifecycle.lifecycle import const, field, lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Counter:
    name: str = const(default="counter")
    count: int = managed(default=0)
    note: str = field(default="")


manager = TransactionManager()
counter = Counter(transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    counter.count = 1
    assert counter.count == 1
    assert counter.working.count == 1
    assert counter.current.count == 0

assert counter.current.count == 1

try:
    with manager.begin(DEFAULT_TRANSACTION):
        counter.count = 2
        counter.note = "attempted update"
        raise ValueError("abort this attempt")
except ValueError:
    pass

assert counter.count == 1
assert counter.note == "attempted update"  # Plain fields are not rolled back.
```

Managed-field assignment outside its active transaction raises. Its default
key is `DEFAULT_TRANSACTION`; `managed(other_key, ...)` chooses another key.
A manager supplied to an object must know that key. Only enlisted participants
are completed; sharing a manager does not make plain fields transactional.

The manager owns completion. Calling `counter.commit(key)` delegates to that
manager and can complete other objects enlisted under that key. Prefer
manager-owned scopes when objects share a manager. Omitting keys selects the
default key and all configured keys; specify keys to keep the boundary explicit.
Multiple keys complete independently, not atomically as a group.

Nested scopes on the same key join one transaction, not savepoints. An inner
abort aborts that key's joined transaction; do not catch it and expect the
outer transaction to remain usable. Access to shared managers/state must be
serialized; this API does not provide thread/task isolation.

## Choose A View

`counter` and `counter.default` provide the ordinary overlay-aware view.
`counter.current` reads committed managed values and rejects their replacement.
`counter.working` reads pending values with committed fallback.

These are live views, not snapshots. Holding `counter.current` does not pin an
old version. Plain fields, binding values, and scratch fields use shared
non-transactional storage across the views. User methods can still mutate
those fields or have external side effects when called on a current facade.

`const` prohibits replacing its stored reference, not changing the contents of
a mutable object it references. It is not recursive freezing.

## Edit An Aggregate

```python
@lifecycle
class Numbers:
    items: tuple[int, ...] = managed(default=(), thaw=list, freeze=tuple)


numbers = Numbers(transaction_manager=manager)
with manager.begin(DEFAULT_TRANSACTION):
    numbers.working.items.append(3)
    assert numbers.current.items == ()

assert numbers.current.items == (3,)
```

Working access in an active transaction creates the editable representation.
Outside a transaction it returns the committed representation. Default-facade
reads do not initiate thawing. For aggregates, use `.working` to request the
editable view and supply conversions that separate mutable data sufficiently.
Tuple/list conversion is shallow, not deep-copy isolation. Do not retain and
reuse mutable working references across transaction boundaries.

Validation/preparation can reject an update before publication. Failures after
publication cannot undo committed values. The current implementation has
multi-participant cleanup/hook failure limitations; do not rely on every
participant being cleaned up after an exceptional completion. Those limitations
are separate from the ordinary edit/commit/abort contract shown above.

## Initialization Lifetimes

`default_factory` computes a value during construction, except for lazy static
initialization. Named parameters request declared field/input providers; they
do not establish a continuously recomputed formula. Supplying a constructor
value skips that field's construction factory. An `init=False` construction
factory still runs. Transient `working_default_factory` initializes a
transaction-local value for each transaction in which it is accessed.

## Proposed Changes: Not Available Yet

Constructor spelling could differ from the property name:

```python
_slot_id: object = const(init_name="slot_id", default=None)
```

The proposed constructor accepts `slot_id`; the property remains `_slot_id`.
This creates no `slot_id` property or factory provider. `init_name` defaults
to the declared field name for new fields, inherits on overrides, and requires
`init=True`. Duplicate constructor names and inherited renaming are rejected.
Existing markers currently reject this new option; use the existing initvar
and copying-factory pattern until it is implemented.

Current `static` fields are lazy/write-once. Whether they should permit
replacement is an open discussion, not a selected change. One alternative is
lazy ordinary storage: first read initializes an unset value, and later writes
replace it immediately without rerunning its factory. Reset, invalidation, and
automatic recomputation are different behaviors and are not implied by that
alternative. Keep using the current write-once contract until a decision is made.
