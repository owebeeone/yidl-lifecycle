from yidl_lifecycle.lifecycle import const, initvar, lifecycle, managed


@lifecycle
class Rectangle:
    area: int = initvar()
    width: int = const(default=4)
    height: int = managed(default_factory=lambda area, width: area // width)
    initial_area: int = const(default_factory=lambda area: area)


rectangle = Rectangle(area=20)
print(rectangle.width, rectangle.height, rectangle.initial_area)

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

# Named classvar values differ from marker attributes on the original class.
from yidl_lifecycle.lifecycle import LifecycleDefinitionError, LifecycleMarker, classvar


@lifecycle
class Providers:
    SCALE: int = classvar(default=4)
    doubled: int = const(default_factory=lambda SCALE: SCALE * 2)
    type_label: str = const(default_factory=lambda cls: cls.__name__)
    original_declaration: object = field(default_factory=lambda cls: cls.SCALE)


providers = Providers()
assert providers.doubled == 8
assert providers.type_label == "Providers"
assert isinstance(providers.original_declaration, LifecycleMarker)
assert Providers.SCALE == 4

try:
    @lifecycle
    class BadOrder:
        optional: int = field(default=1)
        required: int
except LifecycleDefinitionError as error:
    assert "non-default" in str(error)
else:
    raise AssertionError("required field after a default should fail decoration")


@lifecycle
class RequiredFirst:
    required: int
    optional: int = field(default=1)


assert RequiredFirst(3).required == 3


@lifecycle
class Base:
    optional: int = field(default=1)


try:
    @lifecycle
    class BadExtension(Base):
        required: int
except LifecycleDefinitionError as error:
    assert "non-default" in str(error)
else:
    raise AssertionError("inherited defaults also constrain constructor order")


@lifecycle
class UnsetLazy:
    value: int = lazy()


unset = UnsetLazy()
try:
    unset.value
except AttributeError:
    pass
else:
    raise AssertionError("uninitialized lazy read should raise")
unset.value = 3
assert unset.value == 3
print("named/class providers, constructor ordering and unset lazy checks passed")
