# Transaction Scope Ownership

## Supported Check

`TransactionManager.require_sole_transaction_owner(transaction)` succeeds only
when that exact `LifecycleTransaction` is active on its `tx_key`, the key is
not completing, and exactly one begin remains outstanding. It returns `None`
on success and raises `RuntimeError` otherwise. It does not validate, enlist,
prepare, publish, discard, or change a begin count. Other keys are unaffected.

This is a synchronous observation, not a lock or lease. An execution owner
must check again after user callbacks and before certifying completion or
reuse. Token identity is essential: an integer transaction ID alone is not an
ownership certificate. IDs are per key, not globally unique.

## Scope Exits

Both single-key and multi-key `begin` scopes retain their original transaction
objects. An ordinary exit for a transaction that has already ended raises
`RuntimeError` without changing a replacement transaction. An exceptional stale
exit does nothing and returns `False`, preserving the original body exception.
This lets enclosing scopes unwind after an inner rollback without masking the
failure or rolling back a newer transaction on the same key.

Valid nested begins still share one transaction and decrement the same-key
count on successful exit. A rollback discards that entire key; scopes remaining
on the call stack become stale. Multi-key exits attempt each original token in
reverse entry order and aggregate completion errors. This remains independent
per-key completion, not atomic publication across keys.

## Completion Callbacks

While a key prepares/applies/finishes commit or rollback, reentrant same-key
begin, commit, and rollback are rejected. A multi-key begin preflights that
restriction before opening any requested key. Independent other-key operations
remain available. Normal `commit` also fences the original token after
validation: a validator cannot replace it and have the replacement committed
by the old call.

This does not redesign validation, enlistment, participant preparation,
exception aggregation, or publication recovery. In particular, a
`commit_only` exception does not provide a supported phase-aware certificate
that no participant published. Callers must not invent an undo or certify safe
retry from that exception alone.

## Verification

`tests/test_transaction_yidl.py` covers stale ordinary/exceptional single-key
and multi-key exits, caught nested failure followed by replacement, original
body-error preservation, nonpublishing sole-owner checks, and callback-time
multi-key begin rejection. Pyrolyze separately exercises its private render
owner against this real manager; no live render wiring is part of this change.
