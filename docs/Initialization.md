# Initialize dependent values and lazy fields

Use factories when a default depends on another declared input, or when a value
should be computed only on first use. A factory computes an initial value; it
does not install a formula that updates whenever its dependencies change.

## Request inputs by name

This complete example uses a construction-scoped input to initialize two fields:

```python
from yidl_lifecycle.lifecycle import const, initvar, lifecycle, managed


@lifecycle
class Rectangle:
    area: int = initvar()
    width: int = const(default=4)
    height: int = managed(default_factory=lambda area, width: area // width)
    initial_area: int = const(default_factory=lambda area: area)


rectangle = Rectangle(area=20)
print(rectangle.width, rectangle.height, rectangle.initial_area)
```

It prints `4 5 20`. Factory parameter names identify declared providers.
`area` is available to both factories but is not a public retained value field;
do not use attribute access or `hasattr` to retrieve or detect an input's value.
Dependencies are resolved by name, including fields declared later. Cycles and
unknown provider names are definition errors.

Supplying `height=7` skips that field's factory. It does not change `initial_area`.
An `init=False` field has no constructor parameter, but its construction factory
still runs. An `initvar(init=False, default_factory=...)` can provide an internal
construction value without asking the caller for it.

Factories may request a class provider named `cls`. It is the original
undecorated class, useful for information such as `cls.__name__`. Its field
marker attributes are still declarations; they are not initialized provider
values. To receive a classvar's value, name that provider directly:

```python
from yidl_lifecycle.lifecycle import classvar, const, lifecycle


@lifecycle
class Scaled:
    SCALE: int = classvar(default=4)
    doubled: int = const(default_factory=lambda SCALE: SCALE * 2)
    type_label: str = const(default_factory=lambda cls: cls.__name__)


scaled = Scaled()
assert scaled.doubled == 8
assert scaled.type_label == "Scaled"
```

Instance-aware
construction factories requesting `self` must opt in with
`allow_self_factory=True`. Prefer named field dependencies when possible:
the engine cannot infer dependencies hidden inside arbitrary `self` access.
Do not read an as-yet-uninitialized field from such a factory.

Put required constructor fields before fields with constructor defaults or
factories, including when extending a decorated base. Otherwise the generated
constructor cannot be defined and decoration raises `LifecycleDefinitionError`.
This ordering rule is separate from factory dependency order: provider names
may refer forward, but the resulting constructor must still be valid Python.
Lazy fields count as defaulted constructor parameters for this rule, including
`lazy()` without a default or factory.

## Lazy values

A lazy field waits until its first read unless the constructor or an assignment
already supplied its value. This standalone example shows the timing:

```python
from yidl_lifecycle.lifecycle import field, lazy, lifecycle


@lifecycle
class Report:
    title: str = field(default="draft")
    heading: str = lazy(default_factory=lambda title: title.upper())
    cache: dict[str, int] = lazy(default_factory=dict, mutable=True)


report = Report()
report.title = "ready"
assert report.heading == "READY"
report.title = "later"
assert report.heading == "READY"
report.cache = {"hits": 1}
print(report.heading, report.cache["hits"])
```

It prints `READY 1`. The factory reads provider values visible at first access,
then caches the result. Later provider changes do not invalidate it. Assignment
before first read bypasses the factory. Later replacement raises by default;
`mutable=True` permits replacement without rerunning the factory. A failed
factory read does not install a successful cached value.

Both policies are nontransactional. Rollback does not reset a lazy cache.
Write-once storage also does not recursively freeze the cached object's contents.
With `lazy()` and no supplied value, default or factory, construction can still
succeed, but reading the uninitialized value raises `AttributeError`. Supply a
value through the constructor or first assignment before reading it.
`static` is an exact compatibility alias; use `lazy` in new declarations.
Lazy factories currently cannot directly depend on an `initvar`. Retain the
needed value in a suitable field instead. Transient working factories have
separate private-retention support for initialization inputs.

## Transaction-local values

Use `transient` when a transaction needs scratch data that must not become
the next committed value:

```python
from yidl_lifecycle.lifecycle import lifecycle, transient
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Edit:
    scratch: list[str] | None = transient(
        default=None, working_default_factory=list
    )


manager = TransactionManager()
edit = Edit(transaction_manager=manager)
with manager.begin(DEFAULT_TRANSACTION):
    edit.working.scratch.append("temporary")
    assert edit.current.scratch is None
assert edit.scratch is None

with manager.begin(DEFAULT_TRANSACTION):
    assert edit.working.scratch == []
print(edit.scratch)
```

It prints `None`. The working factory runs when the transaction-local value is
first needed; commit and rollback both discard that working value. Ordinary
`default`/`default_factory` supplies the baseline. Working factories can
request named providers and `self`, `current`, or `working` views.

For persistent nontransactional scratch storage instead, choose
`local_store(default_factory=dict)`. It is shared by all views and survives
rollback. Unlike a transient working factory, it initializes with the instance.

See the [field signatures and option rules](Markers.md), and the complete
[initialization example](../examples/initialization.py).
