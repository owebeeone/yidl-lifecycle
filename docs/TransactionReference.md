# Transaction API reference

Use [coordinating objects](Transactions.md) for worked examples.
Import managers, tokens, completion evidence and validation errors from
`yidl_lifecycle.transaction_yidl`; import field/hook functions from
`yidl_lifecycle.lifecycle`.

## Manager construction and key selection

```text
TransactionManager(*, tx_keys=())
```

Creates a manager supporting `DEFAULT_TRANSACTION` plus the supplied hashable
custom keys. Duplicate keys are normalized. `manager.tx_keys` lists configured
custom keys; it does not repeat the implicit default key. Unknown operation keys
raise `RuntimeError`. Use stable hash/equality for keys.

Every operation below accepts zero or more positional keys. **No keys means
the default key and all configured custom keys**, not just the default.
Prefer explicit keys. Different keys complete independently, even when selected
in one call. Sharing a manager does not make ordinary fields transactional.

## begin

```text
manager.begin(*keys)
```

Opens or joins transactions immediately. For one selected key it returns a
`LifecycleTransaction`, also usable as a context manager. Normal scope exit
requests validated commit; exceptional exit requests rollback and propagates
the body exception. With several selected keys it returns a combined scope,
not a single token with one completion record.

A nested begin on the same key joins the existing transaction and increases its
begin count. Inner success closes a level; only outermost completion publishes.
Rollback aborts the joined key immediately, not just the innermost changes.
Scopes are bound to the transaction they began: a stale scope must not complete
a replacement transaction.

Use the manager to finish an explicit begin. Mixing manual completion with an
active `with` scope risks stale/double completion. Managers provide no thread
or async-task isolation; callers must serialize shared access.

## validate

```text
manager.validate(*keys) -> None
```

Runs validators against the current candidate without publication or completion.
Requires active transactions. Validation failures raise and can be grouped;
a subsequent edit can invalidate a previous successful check. This is not a
reservation or an authorization to skip later validation.

## commit and commit_only

```text
manager.commit(*keys)
manager.commit_only(*keys)
```

`commit` validates at outermost completion, prepares participants and publishes
managed replacements if preparation succeeds. `commit_only` follows the same
completion path **without validation**; its caller assumes that responsibility.

For one key, returns the completed transaction ID (`int`), or `None` when
only closing a nested begin level. Several keys return a tuple of those results
in normalized key order, if all selected completions succeed. No active
transaction raises `RuntimeError`. Failures from several keys can be grouped;
a failure does not undo already successful keys.

Validation precedes preparation, including before-commit hooks. A before hook
must not rely on a second validation pass after its own changes. Keep changes
within the intended invariant. Eligible after-commit actions run after publication.

## rollback

```text
manager.rollback(*keys)
```

Discards pending values for each selected active key and invokes eligible
after-rollback actions. Returns its completed transaction ID, or a tuple for
several keys. A rollback ends that key's joined transaction regardless of nesting.
No active transaction raises `RuntimeError`. Callback/cleanup errors propagate,
possibly grouped. Arbitrary effects of callbacks and resource acceptance are not
reversed.

## Inspect a transaction

```text
manager.active_transaction
manager.active_transaction_for(tx_key=DEFAULT_TRANSACTION)
manager.begin_count
transaction.tx_id
transaction.tx_key
transaction.completion
```

`active_transaction` and `begin_count` describe the default key; use
`active_transaction_for` for a custom key (its argument is named `tx_key`).
The active token is `None` outside an edit. `completion` is initially `None`
and later contains immutable terminal evidence retained on the token. See
[the field-by-field completion guide](Resources.md#inspect-completion).

Treat tokens as observations, not mutable application data. Do not replace manager
state or modify transaction membership. Low-level enlist/drop operations support
generated participants; ordinary application field writes enlist automatically.

## Completion and errors

`YidlValidatorReturnedFalse` is a `RuntimeError` subclass carrying the rejected
`context`. Validators, factories, conversions and hooks can raise their own
exceptions. Multiple failures can be retained as an `ExceptionGroup` or
`BaseExceptionGroup`; inspect nested exceptions rather than assuming one error
type describes every failure.

The engine attempts eligible discard and after actions while retaining failures.
An after-hook failure can be reported after publication. A protocol/ownership
failure can prevent safe completion. An exception alone does not prove rollback
or cleanup; retain the single-key token and examine `completion`.
No general repair operation or automatic compensation for external effects is
provided.

Application state should remain serialized throughout edits and completion.
Callbacks must not recursively begin/complete edits, replace ownership or mutate
participant membership. Controlled candidate writes are allowed in before hooks,
not arbitrary writes during completion.

## Object helpers and live views

Generated objects expose `begin`, `validate`, `commit`, `commit_only` and
`rollback` helpers delegating to their manager. Completing through one object
can therefore complete other enlisted objects under that key. Prefer explicit
manager ownership for shared edits.

`model.default`, `model.current` and `model.working` are live facades over the
same state, not history frames. Their managed read/write policies are documented
in [concepts](Concepts.md#three-ways-to-read-the-same-state).
