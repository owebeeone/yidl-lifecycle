# ManagedContext: Transaction-Scoped Editing

Status: user-facing DRAFT, 2026-10-03. Existing API is shown first. Proposed
constructor aliases at the end are not implemented yet.

Pyrolyze's LCM runtime locally aliases the library's `lifecycle` decorator as
`managed_context`. The older `pyrolyze.lifecycle.managed_context` is a separate
legacy implementation with different marker objects; it is not interchangeable
with the imports used on this page.

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

For a custom key, configure the manager explicitly:

```python
EDITS = "edits"


@lifecycle
class CustomCounter:
    count: int = managed(EDITS, default=0)


edit_manager = TransactionManager(tx_keys=(EDITS,))
custom = CustomCounter(transaction_manager=edit_manager)
with edit_manager.begin(EDITS):
    custom.count = 1
assert custom.current.count == 1
```

The manager owns completion. Calling `counter.commit(key)` delegates to that
manager and can complete other objects enlisted under that key. Prefer
manager-owned scopes when objects share a manager. Omitting keys selects the
default key and all configured keys; specify keys to keep the boundary explicit.
Multiple keys complete independently, not atomically as a group.

Outermost `commit` and normal outermost scope exit validate before publication.
`commit_only` is an advanced operation that **bypasses validators** and can
publish a rejected value. Its completion owner assumes validation
responsibility; a prior `validate` does not certify edits made afterward.
Use `commit` or an ordinary manager scope for normal completion.

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

For the reference graph and facade collection rules, see
[Lifecycle facades: references and lifetime](FacadeOwnership.md).

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

For healthy state with no stale overlay, working access in an active transaction
creates the editable representation; outside it, access returns committed
representation. Default-facade reads do not initiate thawing. For aggregates,
use `.working` to request the
editable view and supply conversions that separate mutable data sufficiently.
Tuple/list conversion is shallow, not deep-copy isolation. Do not retain and
reuse mutable working references across transaction boundaries.

Validation/preparation can reject an update before publication. Failures after
publication cannot undo committed values. The current implementation has
multi-participant cleanup/hook failure limitations; do not rely on every
participant being cleaned up after an exceptional completion. Those limitations
are separate from the ordinary edit/commit/abort contract shown above.

Interrupted cleanup can leave stale working values visible even after the
manager becomes inactive. Starting another transaction does not repair them:
getters can return the stale value without enlistment, and assignment can
reject the old token. Dropping previously returned lists is not sufficient.
Stop reusing the affected state cohort until cleanup or supported recovery is
verified; this API currently provides no general guaranteed-recovery command.

`owned` adds another boundary: candidate resources are accepted during prepare,
before their references become current. A later prepare failure can leave a
candidate accepted while its current reference remains unchanged. A map can be
partially accepted. Rollback of the reference does not undo those resource
effects; a failed commit is not proof that candidates were never accepted.

## Initialization Lifetimes

`default_factory` computes a value during construction, except for `lazy`
initialization. Named parameters request declared field/input providers; they
do not establish a continuously recomputed formula. Supplying a constructor
value skips that field's construction factory. An `init=False` construction
factory still runs. Transient `working_default_factory` initializes a
transaction-local value for each transaction in which it is accessed.

`lazy` is the preferred spelling for per-instance lazy storage;
`static` remains an exact compatibility alias. A constructor value or first
assignment initializes the field. Otherwise, first read uses its default or
calls its factory with the provider values visible at that access. The result
is cached, and later assignments raise unless `mutable=True`. With that option,
assigning before first read bypasses the factory, and later assignments replace
the cached value immediately through any facade. Replacement does not rerun the
factory; dependency changes do not trigger recomputation. Both policies remain
nontransactional. The internal field kind and generated diagnostics retain
`static` for compatibility.

```python
cache: dict[str, int] = lazy(default_factory=dict, mutable=True)
```

## Proposed Changes: Not Available Yet

Constructor spelling could differ from the property name:

```python
_slot_id: object = const(init_name="slot_id", default=None)
```

The proposed constructor accepts `slot_id`; the property remains `_slot_id`.
This creates no `slot_id` property or factory provider. `init_name` defaults
to the declared field name for new fields and inherits on overrides. `const`
defaults to `init=True`, so the example satisfies the prerequisite. An explicit
non-`None` alias requires `init=True`; `init=False` with the default `init_name=None`
still creates no constructor parameter. Duplicate constructor names and
inherited renaming are rejected.
Existing markers currently reject this new option; use the existing initvar
and copying-factory pattern until it is implemented.
