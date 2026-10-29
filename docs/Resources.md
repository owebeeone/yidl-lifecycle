# Resources, ownership and failure recovery

Use ordinary `managed` for model values. Binding fields are an advanced route
for retained resources implementing Lifecycle's `BindingBase` protocol. They
do not make file descriptors, network calls or arbitrary external effects
transactional.

## Choose binding or owned

Import resource base/container types from `yidl_lifecycle.bindings`, and markers
from `yidl_lifecycle.lifecycle`.

- `binding` stores a resource reference nontransactionally.
- `owned` manages replacement of a retained resource reference under a key.
  It accepts a `BindingBase` value or a supported annotated resource map.
- A `BindingBase` resource has `accepted()`, `is_accepted` and `is_closed`.
  A subclass can implement `_close()` for cleanup. Its destructor invokes
  cleanup, but application references and the Python runtime determine when
  release becomes possible. Do not treat facade collection as an explicit close.

Acceptance happens during preparation, before the candidate reference becomes
current. If a later participant fails, an earlier candidate may already be
accepted even though its reference was never published. An annotated resource
map can be partially accepted. Rolling back references does not reverse those
resource effects.

Use explicit application-level lifetime management for effects that need a
deterministic close or compensation. The detailed [ownership reference](FacadeOwnership.md)
explains which view references can retain model state. Container implementation
and integration evidence remain in [developer documentation](../dev-docs/README.md).

## Inspect completion

For recovery-sensitive operations, retain the token from an explicit single-key
begin. This complete example deliberately fails a notification after publishing:

```python
from yidl_lifecycle.lifecycle import after_commit, lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Model:
    value: int = managed(default=0)

    @after_commit(DEFAULT_TRANSACTION)
    def notify(self) -> None:
        raise ValueError("notification failed")


manager = TransactionManager()
model = Model(transaction_manager=manager)
transaction = manager.begin(DEFAULT_TRANSACTION)
model.value = 4
try:
    manager.commit(DEFAULT_TRANSACTION)
except ValueError:
    evidence = transaction.completion
    assert evidence.publication_complete
    assert not evidence.after_actions_complete
    print("notification failed; committed value:", model.value)
```

It prints `notification failed; committed value: 4`. Retrying the entire edit
would repeat work that has already been published. The complete
[validation example](../examples/validation.py) contrasts this with rejection
before publication. The [resource example](../examples/resources.py) separately
demonstrates owned-reference acceptance and cancellation before preparation.

`transaction.completion` is `None` until terminal evidence has been recorded.
It remains available after manager finalization. Its fields distinguish:

| Field | What it records |
| --- | --- |
| `tx_key`, `tx_id` | The edit being completed |
| `publication_started`, `publication_complete` | Whether publication started and finished |
| `discard_complete` | Whether discard completed |
| `after_actions_complete` | Whether eligible after actions completed |
| `ownership_preserved` | Whether completion retained its expected ownership |
| `finalized` | Whether manager finalization completed |
| `failures` | Retained exceptions from completion |

A completed publication followed by an after-hook failure requires different
recovery from rejection before publication. Inspect the fields together and
report retained failures; one Boolean alone does not certify all cleanup.

An ownership/protocol error can make safe completion impossible. Do not silently
reuse an uncertain group of states or repeatedly retry as though rollback were
known to have succeeded. There is no general repair command. The
[transaction reference](TransactionReference.md) describes scope ownership;
[troubleshooting](Troubleshooting.md) covers common symptoms.
