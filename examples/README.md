# Runnable Lifecycle examples

Install the package and select the backend as described in
[getting started](../docs/GettingStarted.md#install). From this repository root,
run an example with `python examples/settings.py`.

| Script | What to observe |
| --- | --- |
| [settings.py](settings.py) | Two-field edit, rollback, write guard, explicit manager completion |
| [views.py](views.py) | Ordinary field survives rollback; a retained current view follows commits |
| [collections.py](collections.py) | Working list, committed tuple, discarded collection edit |
| [transactions.py](transactions.py) | Shared objects, explicit completion, nested scopes and custom keys |
| [initialization.py](initialization.py) | Named inputs, lazy timing and transaction-local scratch |
| [validation.py](validation.py) | Rejection versus failure after successful publication |
| [resources.py](resources.py) | Owned resource acceptance and cancellation before preparation |

Each script is standalone, contains assertions and prints its result. These are
application examples, not instructions for regenerating the library.
