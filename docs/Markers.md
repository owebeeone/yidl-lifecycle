# Field and hook reference

Import these functions from `yidl_lifecycle.lifecycle`. Each field function
returns a declaration consumed by `@lifecycle`, not the eventual stored value.
For a first model, use the [tutorial](GettingStarted.md); for factory examples,
use [initialization](Initialization.md).

## Choose a field policy

| Declaration | Use it for | Effect of rollback |
| --- | --- | --- |
| `field` | Ordinary mutable instance data | No restoration |
| `const` | Initialize once, forbid replacement | Nontransactional |
| `lazy` | Initialize on first use, normally write once | Cached result survives |
| `static` | Compatibility alias for `lazy` | Identical to `lazy` |
| `managed` | Persistent model values changed under a transaction | Discards pending replacement |
| `transient` | A transaction-local working value over a baseline | Discards working value; commit also discards it |
| `owned` | Transaction-managed retained binding resource reference | Discards reference change, not arbitrary resource effects |
| `binding` | Nontransactional binding resource reference | No restoration |
| `local_store` | Per-instance scratch/cache without constructor input | No restoration |
| `initvar` | Input/provider for initialization, not a public field | Not transaction storage |
| `classvar` | Class-level provider/value | Not instance transaction storage |

A bare annotated member such as `count: int` is an ordinary required field;
`count: int = 0` is an ordinary field with a default. Use `managed` explicitly
for transactional data. Annotations do not add automatic conversion or validation.

## Signatures

`MISSING` below means the argument was omitted; do not pass an internal sentinel
to get a default. `None` is a real field value, not the omission marker.

```text
field(*, default=MISSING, default_factory=MISSING,
      allow_self_factory=False, init=True)
const(*, default=MISSING, default_factory=MISSING,
      allow_self_factory=False, init=True)
lazy(*, default=MISSING, default_factory=MISSING,
     allow_self_factory=False, init=True, mutable=False)
static = lazy

managed(tx_key=DEFAULT_TRANSACTION, *, compare="value",
        default=MISSING, default_factory=MISSING,
        allow_self_factory=False, init=True,
        freeze=MISSING, thaw=MISSING)
transient(tx_key=DEFAULT_TRANSACTION, *, compare="value",
          default=MISSING, default_factory=MISSING,
          allow_self_factory=False, working_default_factory=MISSING, init=True)
owned(tx_key=DEFAULT_TRANSACTION, *, compare="value",
      default=MISSING, default_factory=MISSING,
      allow_self_factory=False, init=True)
binding(*, default=MISSING, default_factory=MISSING,
        allow_self_factory=False, init=True)

local_store(*, default=MISSING, default_factory=MISSING)
initvar(*, default=MISSING, default_factory=MISSING,
        allow_self_factory=False, init=True)
classvar(*, default=MISSING)
```

All return a `LifecycleMarker`. Invalid combinations/options raise
`LifecycleDefinitionError` (a `ValueError` subclass), or an ordinary
`TypeError` for an unsupported function argument. Definition errors discovered
during decoration may wrap the underlying generator error; inspect its cause.

## Shared initialization options

| Option | Meaning and constraints |
| --- | --- |
| `default` | Value used when the constructor omits this field. A mutable object is shared if supplied as a literal default; prefer a factory for per-instance containers. |
| `default_factory` | Callable producing an initial value when omitted. Mutually exclusive with `default`. Runs during construction except for lazy fields. |
| `init=True` | Include the field/input in the generated constructor. A supplied value skips its factory. |
| `init=False` | Omit that constructor argument; a declared construction default/factory still initializes it. |
| `allow_self_factory=False` | Construction factory parameter `self` is rejected unless explicitly enabled. Not accepted by `local_store` or `classvar`. |

A required constructor field has neither a default nor a factory. Constructor
arguments can be passed by position or name; `transaction_manager` is keyword-only.
Supplying an unknown keyword raises `TypeError`. Use the resulting class's
Python signature to inspect its exact constructor.

Required constructor fields must precede fields with constructor defaults,
including defaults supplied by factories. Otherwise decoration raises
`LifecycleDefinitionError` for a non-default argument following a default.
This also matters when adding inherited fields. A `lazy()` declaration is an
exception to the required-input rule: it can be omitted without a default or
factory, but reading it before supplying a value raises `AttributeError`.
Lazy fields are optional constructor parameters and count as defaulted fields
for this ordering rule, even when `lazy()` declares no default or factory.

Factories request declared providers by parameter name. Dependencies can be
declared out of order. `cls` requests the original undecorated class; its marker
attributes are declarations, not initialized values. Request a classvar's value
by its declared provider name, not by reading a marker from `cls`.
`self` requires the opt-in
above for construction factories. Special `current`/`working` injection is
not available to ordinary construction factories. It is available to transient
working factories.

Unknown providers, dependency cycles, and unavailable dependencies are rejected.
Parameters must be bindable by name: required positional-only parameters and
variadic `*args`/`**kwargs` are rejected. Optional positional-only parameters
are omitted. Optional parameters of class factories are not treated as required
providers. When a callable's signature cannot be inspected, it is treated as
zero-argument, with `LifecycleDefinitionWarning` except for supported builtin
class factories. Keep factories simple and make dependencies explicit.

## Ordinary, constant and lazy storage

`field` permits immediate replacement through any facade. `const` initializes
during construction and rejects later replacement with `AttributeError`.
Neither participates in a transaction.

`lazy` accepts an initial constructor value or first assignment. Otherwise its
first read uses the default/factory. Further assignment raises `AttributeError`
unless `mutable=True`; that option permits immediate nontransactional
replacement. Provider values are read at first access. Replacement and dependency
changes do not rerun the factory. Failed factory evaluation does not cache a
successful result.

Neither constant nor lazy storage recursively freezes mutable contents.
`static` is an exact alias; internal errors can still use that older name.

## Managed values and conversion

`tx_key` selects the edit group. Custom keys must be hashable and registered
on the supplied manager. Managed assignment outside the matching active
transaction raises `RuntimeError`; assignment through `.current` raises
`AttributeError`.

`compare="value"` uses value equality to detect redundant assignments;
`compare="identity"` uses object identity instead. This is transaction write
detection, not generation of model equality or ordering methods. It does not
detect arbitrary in-place mutations of a shared object.

Only `managed` accepts `thaw` and `freeze`. Each must be callable when
provided. Working access uses `thaw(committed_value)` to obtain an editable
representation. Preparation uses `freeze(working_value)` to produce the
candidate committed representation. They are not type coercion/validation on
every assignment. Nullable managed annotations have a special `None` path
that bypasses conversion for `None`. See [collections and aliasing](Collections.md).

Ordinary reads do not initiate thawing. Obtain editable aggregate storage through
`.working` in an active transaction and discard escaped working references when
the edit ends.

## Transient and local storage

`transient` has a baseline initialized by `default`/`default_factory`, plus a
transaction-local overlay. `working_default_factory` initializes that overlay
on first use in an edit. It may request declared providers or `self`, `current`
and `working` views. An initialization input needed by this working factory can
be retained privately. Commit and rollback both discard the overlay; neither
publishes it into the baseline. A transaction is required for replacement.

`local_store` initializes nontransactional scratch storage with the instance,
has no constructor parameter and accepts only `default` or `default_factory`.
Named dependencies are supported for its factory; `allow_self_factory` and
`working_default_factory` are not accepted. It survives all transaction outcomes.

## Initialization inputs and class values

`initvar` is a named initialization provider, not a public instance attribute.
With `init=False`, it must have a default or factory. It can initialize multiple
fields. Lazy factories currently cannot directly depend on an `initvar`;
materialize the needed value in a retained field instead. Transient working
factories have separate private-retention support.

`classvar(default=...)` supplies class-level data and can be a named provider.
It has no instance constructor parameter, factory or transaction policy.
These are Lifecycle marker functions; do not substitute stdlib dataclass field
objects or markers from older Pyrolyze APIs.

## Binding resources

`binding` and `owned` support retained `BindingBase` values and supported
annotated resource maps. `binding` is nontransactional; `owned` is managed
under its key and accepts resources during preparation. Acceptance and external
effects are not reversed by reference rollback. See [resources and recovery](Resources.md)
before using these kinds.

## Hooks

All five decorators accept the same call forms:

```text
@commit_order_key()                 # Default key
@validate_commit(MY_KEY)            # Positional key
@before_commit(tx_key=MY_KEY)       # Keyword key
@after_commit()
@after_rollback()
```

Each returns a method decorator. The method is an instance method with no
additional required arguments. An ordering method supplies a comparable key;
a validator supplies a Boolean; other hook return values are ignored.
Larger participant ordering keys complete first. Invalid decorator call shapes
raise `LifecycleDefinitionError`. Use parentheses, including for the default key.

Read [validation and hook timing](Hooks.md) for examples and the
[completion reference](TransactionReference.md#completion-and-errors) for failure
semantics. `commit_only` bypasses validators.

## Decorator, inheritance and reserved names

`lifecycle(cls)` returns the generated class; use it as `@lifecycle`, without
decorator options. Non-class arguments raise `TypeError`. User methods remain
available through the generated views. Decorated subclasses inherit Lifecycle
field policies and hooks. An inherited managed field must remain managed under
the same transaction key if redeclared.

Do not declare fields called `current`, `working`, `default`, generated
transaction helpers, or names using the reserved `_y_` / `__yidl_...__` prefixes.
The decorator rejects collisions rather than silently replacing its machinery.

## Not an available option

Constructor aliases such as `init_name` remain [proposals](Proposals.md) and
are rejected by current markers. Lifecycle has no Dataclass-style global frozen
switch, permanent `freeze()` operation or Undoable-style frame navigation.
