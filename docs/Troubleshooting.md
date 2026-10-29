# Troubleshooting Lifecycle

Start with the symptom. The linked guide explains the underlying rule and a
complete supported example.

| Symptom | Explanation | Action |
| --- | --- | --- |
| Managed assignment says “writes require an active yidl transaction” | No matching active key on this object's manager | Begin that key on the same manager, edit, then commit or roll back. See [transactions](Transactions.md). |
| Assignment through `.current` raises | Committed managed access rejects replacement | Edit through the default or working view inside its transaction. |
| A field kept its new value after rollback | It is ordinary/lazy/local storage, or an earlier edit was already committed | Choose `managed` for values that need rollback; distinguish cancelling a pending edit from undoing history. See [concepts](Concepts.md). |
| A list changed despite rollback | Its mutable contents were shared, or were changed without requesting working storage | Use `thaw`/`freeze` and `.working`; isolate nested mutable elements too. See [collections](Collections.md). |
| A saved current view shows new values | Facades are live | Copy application values if you need an independent snapshot. |
| “unknown yidl transaction key” | The manager does not know the key used by the field/operation | Register it in `TransactionManager(tx_keys=(KEY,))` and pass that manager to all relevant objects. |
| An inner failure leaves no active outer transaction | Same-key scopes join; rollback aborts the whole key | Let the failure leave the outer operation. Do not treat nested scopes as savepoints. |
| Lazy replacement raises `AttributeError` | Lazy fields are write-once by default | Supply the desired initial value, or deliberately declare `mutable=True`. |
| A factory is not rerun after its input changes | Factory dependencies initialize; they are not reactive formulas | Recompute explicitly if your application needs a later update. |
| Factory decoration reports an unknown name or cycle | Parameter names are provider declarations | Match declared provider names and remove cycles. See [initialization](Initialization.md). |
| Lazy factory cannot use an initvar | Lazy initvar dependencies are not currently supported | Retain the needed input in a suitable field and depend on that field. |
| `local_store` rejects an option | It has no `init`, `allow_self_factory` or working-factory option | Use only its documented defaults/factory options; use `transient` for transaction-local data. |
| Commit raised but values changed | An after hook may have failed after publication | Inspect the retained token's [completion evidence](Resources.md#inspect-completion); do not retry blindly. |
| An owned resource was accepted during a failed commit | Resource acceptance precedes reference publication | Inspect the resource state and implement application compensation/lifetime policy. See [resources](Resources.md). |
| Definition says `init_name` is unsupported | It is a proposal, not a supported marker argument | Use the current Python constructor field name. |
| Import/decorating fails after dependency changes | The release qualifies exact dependency versions | Reproduce in a clean virtual environment with the published package; do not substitute arbitrary SDK versions. |
| Package installation fails on Windows Python 3.15 | Astichi 1.1.3 lacks a qualified binary wheel for that combination | Use a qualified Python/platform combination; source-building that dependency is a separate, unqualified route. See [support](GettingStarted.md#install). |

For cache misses, persistence settings, clearing and stale running processes,
use [cache troubleshooting](Cache.md#troubleshooting). Disabling persistence
does not fix an invalid model declaration or incompatible dependencies.

When reporting a problem, include the smallest model that reproduces it, Python
and package versions, the selected backend, the exact operation/key, and the
exception chain/group. Remove application secrets. For completion failures,
include which publication/discard/after-action flags were recorded.
