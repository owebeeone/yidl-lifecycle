# Validate an edit and react to completion

Use a validator when a combination of managed values must satisfy an invariant.
Use completion hooks for notifications associated with commit or rollback.
Read [transaction boundaries](Transactions.md) first.

Validation and hooks apply to **enlisted participants**, not every object that
shares the manager. Construction does not invoke commit validation. An untouched
object is not automatically checked by `validate` or commit, and assigning an
equal managed value can return before enlistment. Plain-field edits do not
enlist the object either. A changed managed replacement or materializing an
editable working value can enlist it. Merely entering a transaction is not an
instruction to validate your entire model.

If your application must check initial or unchanged data, run its business
validation explicitly as well. Do not rely on a redundant assignment to force
hooks. The [validation example](../examples/validation.py) demonstrates a
no-op transaction over an initially invalid value.

## Reject an invalid candidate

The validator sees pending values. This complete example rejects a negative count:

```python
from yidl_lifecycle.lifecycle import lifecycle, managed, validate_commit
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Stock:
    quantity: int = managed(default=1)

    @validate_commit(DEFAULT_TRANSACTION)
    def valid_quantity(self) -> bool:
        return self.quantity >= 0


manager = TransactionManager()
stock = Stock(transaction_manager=manager)
transaction = manager.begin(DEFAULT_TRANSACTION)
stock.quantity = -1
try:
    manager.commit(DEFAULT_TRANSACTION)
except ExceptionGroup:
    assert stock.quantity == 1
    assert transaction.completion.discard_complete
    print("rejected:", stock.quantity)
```

It prints `rejected: 1`. A false validator result is reported as
`YidlValidatorReturnedFalse`, possibly inside an exception group. The manager
attempts discard before reporting completion failure. Application recovery must
inspect completion evidence when cleanup or user callbacks can also fail.

Normal outermost scope exit and `manager.commit` perform validation.
`manager.validate` checks the current candidate without publishing it; subsequent
edits can make that result obsolete. Advanced `commit_only` bypasses validation
and must not be used as the normal completion path.

## Declare hooks beside their methods

The decorators are imported from `yidl_lifecycle.lifecycle`:

| Decorator | Method result | Purpose |
| --- | --- | --- |
| `@commit_order_key(key)` | Comparable ordering key | Order participants; larger keys complete first |
| `@validate_commit(key)` | Boolean | Accept or reject a candidate before publication |
| `@before_commit(key)` | Ignored | Prepare/normalize the candidate before publication |
| `@after_commit(key)` | Ignored | React after publication |
| `@after_rollback(key)` | Ignored | React after discard |

Use zero-argument instance methods other than `self`. Call each decorator:
`@after_commit()` selects the default key, and
`@after_commit(tx_key=MY_KEY)` selects a registered custom key.
Bare `@after_commit` is not the supported form. Hooks for different keys are
separate; they do not turn those keys into one atomic group.

A continuation of the Stock class could declare an `after_commit` method that
notifies a view of the new quantity. The [complete hook example](../examples/validation.py)
shows this alongside a rejected candidate and a failed after hook.

## Keep side effects explicit

Before-commit hooks have a controlled candidate-write window. They are not a
place to start another transaction, change manager membership or finish the
current edit recursively. Validators should check candidates, not perform
external effects or assume a single invocation.

Validation runs before preparation, including before-commit hooks. Do not assume
a second validation pass will check changes made by a before hook; preserve the
invariant yourself. See the [completion sequence](TransactionReference.md#commit-and-commit_only).

After hooks can fail **after values have already been published or discarded**.
An exception from commit therefore does not prove the model was rolled back.
For an application sending notifications or managing resources, retain the
transaction token and read its [completion evidence](Resources.md#inspect-completion).
Rollback cannot unsend a message or undo a file write made by user code.
