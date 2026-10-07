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
begin, validate, commit, and rollback are rejected. Public standalone validation
is available only outside final completion; it cannot borrow an open before-hook
write window. A multi-key begin preflights that
restriction before opening any requested key. Independent other-key operations
remain available. Normal `commit` also fences the original token after
validation: a validator cannot replace it and have the replacement committed
by the old call.

## Terminal Completion Evidence

The L0 implementation candidate follows
[the accepted completion contract](../../pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md).
Library implementation acceptance and private Pyrolyze consumer adoption remain
separate gates; no live resource route is activated by these library changes.

The original `LifecycleTransaction.completion` retains an immutable
`TransactionCompletion` after final completion, even when completion raises.
Nested nonfinal commits and standalone validation leave it unset. Evidence
records the original key/token, whether application was entered/completed,
discard/after-action completion, ownership/finalization, and original failures.
An application that mutates then raises is not reported as undone.

Key/ID identity is retained from transaction creation, independently of public
token metadata. Reassigning that metadata is unsupported and loses completion
authority; evidence still names the original key/ID, and a replacement active
token is not finalized by the old completion. Diagnostic formatting and exception
notes are best-effort: an overridden annotation method or malformed notes cannot
interrupt cleanup or replace an already retained original failure.

Participants and commit order are captured once. Preparation stops on its first
failure; discard drains all captured participants. Independent applications
continue after an unexpected application error. After actions run only for
participants whose apply/discard succeeded, and each inherited/local generated
after hook has its own error wrapper. All actual failures retain deterministic
context and original exception identity. An exception alone is still not proof
of unpublished discard, safe retry, or atomic multi-key publication.

## Candidate Writes During Completion

The manager tracks captured participants whose field preparation has not begun.
Generated preparation opens `_before_commit_hooks(state, tx_key, tx_token)`
only around before-hook dispatch, closes it in `finally`, and closes that
participant's write permission before converting/staging its fields.

The common generated write helper calls the manager's
`_require_candidate_write(state, tx_key)` before mutation or materializing a
factory/thaw. During completion, before hooks may stage themselves or captured
later/unprepared participants. New enrollment and writes to prepared
participants are rejected, including fields with existing working values or
tokens. Validation, ordering, conversion, application, discard, and after hooks
cannot create candidate values. Other-key permissions remain independent.

Reading an existing overlay is permitted. Mutation through an arbitrary retained
mutable alias is not intercepted: callers must honor the same write boundary.
No proxy, defensive copy, savepoint, or automatic re-preparation is provided.
Legacy participants without the before/field boundary may not stage candidates
during preparation.

## Verification

`tests/test_transaction_yidl.py` covers stale ordinary/exceptional single-key
and multi-key exits, caught nested failure followed by replacement, original
body-error preservation, nonpublishing sole-owner checks, and callback-time
multi-key begin rejection. Pyrolyze separately exercises its private render
owner against this real manager; no live render wiring is part of this change.

The same manager test file covers completion evidence, phase draining,
membership/ownership failures, and invalid/repeated hook-window entry. The
canonical `tests/data/gold_src/yidl_transactional_completion_failures.py` fixture
owns generated inherited-hook composition, permitted before-hook writes,
rejected late/materializing writes, clean discard/reuse, and other-key isolation.
