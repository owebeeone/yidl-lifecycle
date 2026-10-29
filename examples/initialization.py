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
