# Fields and transaction hooks

Import field markers and decorators from `yidl_lifecycle.lifecycle`. A marker is
a declaration harvested when `@lifecycle` runs; it is not the stored field value.
Start with the [counter tutorial](GettingStarted.md) before combining policies.

## Field policies

| Marker | Purpose | Transaction boundary |
| --- | --- | --- |
| `field` | Ordinary per-instance storage | Updates immediately; rollback does not restore it |
| `const` | Reference set during initialization, then protected from replacement | Nontransactional; does not recursively freeze an object |
| `lazy` | Initialize from an explicit value/assignment or the first read | Nontransactional; write-once unless `mutable=True` |
| `static` | Exact compatibility alias for `lazy` | Same policy; prefer `lazy` in new code |
| `managed` | Committed value plus a working overlay | Assignment requires the selected active transaction |
| `transient` | Transaction-local working overlay, optionally initialized by `working_default_factory` | Participates in the selected transaction; not persistent recomputation |
| `owned` | Transaction-managed retained `BindingBase` value or annotated map | Includes resource acceptance; reference rollback does not undo arbitrary resource side effects |
| `binding` | Plain stored `BindingBase` value or annotated map | Nontransactional binding storage |
| `local_store` | Lifecycle-owned scratch storage with no constructor parameter | Nontransactional; accepts default/default factory |
| `initvar` | Constructor input usable by initialization providers | Does not declare a retained instance field |
| `classvar` | Class-level value | Not per-instance transaction storage |

`default` and `default_factory` are alternatives. A required constructor field
has neither. A supplied constructor value skips that field's factory.
`init=False` removes its constructor parameter; it does not by itself suppress
construction-time initialization. Not every marker accepts every option: use
its Python signature, and treat a definition error as an invalid declaration.

Construction factories can request declared providers by parameter name.
`allow_self_factory=True` permits the supported self-aware factory route.
Factories initialize values; they do not establish continuously updated
formulas. For `lazy`, providers are read at first access. For `managed`,
`thaw`/`freeze` can create editable and committed representations; use `.working`
for aggregate edits. See [initialization and aggregate rules](ManagedContextApiDraft.md).

`managed`, `owned` and `transient` accept a transaction key (defaulting to
`DEFAULT_TRANSACTION`) and `compare="value"` or `compare="identity"`.
Custom keys must be registered with the supplied manager. Independently completed
keys are not a single atomic group. See the [custom-key example](ManagedContextApiDraft.md#edit-and-complete-a-transaction).

## Hooks

Mark methods with `@commit_order_key`, `@validate_commit`, `@before_commit`,
`@after_commit` or `@after_rollback`. The default key is used when omitted;
`@validate_commit(tx_key=MY_KEY)` selects a configured custom key, for example.

- The order-key method supplies commit ordering among participants.
- A validator returns a boolean; `False` rejects ordinary completion.
- Before-commit hooks run during preparation, with controlled candidate writes.
- After hooks run for the corresponding completed publication/discard action.
  They can fail after values have become current; they do not make external
  effects reversible.

Use normal manager scopes or `commit` for validated completion. The advanced
`commit_only` operation bypasses validators. Methods, factories and hooks can
have external effects; transaction rollback covers the defined field/reference
policy, not every effect performed by user code.

## Not an available option

Constructor aliases such as `init_name` remain proposed and are rejected by the
current markers. See [proposed constructor aliases](Proposals.md). Older
Pyrolyze marker objects and dataclass field objects are separate APIs and must
not be substituted for these Lifecycle markers.
