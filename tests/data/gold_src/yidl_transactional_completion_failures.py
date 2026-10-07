from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

import black

from support.golden_case import run_multi_source_case
from yidl_lifecycle.bindings import BindingBase
from yidl_lifecycle.lifecycle import (
    _generate_lifecycle_source,
    after_commit,
    after_rollback,
    before_commit,
    commit_order_key,
    field,
    harvest_lifecycle_definition,
    lifecycle,
    managed,
    owned,
    transient,
    validate_commit,
)
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


def _parent_definition(events: list[str], controls: dict[str, object]) -> type:
    def freeze_count(value: int) -> int:
        events.append(f"freeze:{value}")
        if "conversion" in controls:
            controls["conversion"]()
        if value == -1:
            raise controls["prepare_error"]
        return value

    def thaw_items(value: tuple[int, ...]) -> list[int]:
        events.append("thaw")
        return list(value)

    def scratch_factory() -> list[int]:
        events.append("factory")
        return []

    class CompletionParent:
        rank: int = field(default=1)
        control: object = field(default=None)
        count: int = managed(default=0, freeze=freeze_count)
        untouched: int = managed(default=0)
        items: tuple[int, ...] = managed(default=(1,), thaw=thaw_items, freeze=tuple)
        scratch: list[int] | None = transient(
            default=None, working_default_factory=scratch_factory
        )
        resource: BindingBase | None = owned(default=None)
        audit: int = managed("audit", default=0)

        @commit_order_key(DEFAULT_TRANSACTION)
        def _order(self) -> tuple[int, ...]:
            return (self.rank,)

        @validate_commit(DEFAULT_TRANSACTION)
        def _validate(self) -> bool:
            if "validate" in self.control:
                self.control["validate"](self)
            return True

        @before_commit(DEFAULT_TRANSACTION)
        def _before(self) -> None:
            events.append(f"before:{self.rank}")
            if "before" in self.control:
                self.control["before"](self)

        @after_commit(DEFAULT_TRANSACTION)
        def _parent_after_commit(self) -> None:
            events.append(f"parent_commit:{self.rank}")
            if "after" in self.control:
                self.control["after"](self)
            if "commit_error" in self.control:
                raise self.control["commit_error"]

        @after_rollback(DEFAULT_TRANSACTION)
        def _parent_after_rollback(self) -> None:
            events.append(f"parent_rollback:{self.rank}")
            if "rollback_error" in self.control:
                raise self.control["rollback_error"]

    return CompletionParent


def _child_definition(parent: type, events: list[str]) -> type:
    class CompletionChild(parent):
        @after_commit(DEFAULT_TRANSACTION)
        def _child_after_commit(self) -> None:
            events.append(f"child_commit:{self.rank}")
            if "child_commit_error" in self.control:
                raise self.control["child_commit_error"]

        @after_rollback(DEFAULT_TRANSACTION)
        def _child_after_rollback(self) -> None:
            events.append(f"child_rollback:{self.rank}")

    return CompletionChild


def render_case() -> Mapping[str, str]:
    events: list[str] = []
    parent = _parent_definition(events, {})
    child = _child_definition(lifecycle(parent), events)
    sources = {
        "decorator.py": Path(
            "src/yidl_lifecycle/_generated_lifecycle_base.py"
        ).read_text(),
        "generated_parent.py": _generate_lifecycle_source(
            harvest_lifecycle_definition(parent)
        ),
        "generated_output.py": _generate_lifecycle_source(
            harvest_lifecycle_definition(child)
        ),
    }
    for name, source in tuple(sources.items()):
        sources[name.replace(".py", "_prettier.py")] = black.format_str(
            source, mode=black.FileMode()
        )
    return sources


def _builder(source: str) -> Callable[[type], type]:
    namespace: dict[str, object] = {}
    exec(compile(source, "completion_golden", "exec"), namespace)

    def build(cls: type) -> type:
        return namespace["build_lifecycle_class"](
            cls, **harvest_lifecycle_definition(cls).build_kwargs
        )

    return build


def _error(call: Callable[[], object]) -> BaseException:
    try:
        call()
    except BaseException as error:
        return error
    raise AssertionError("expected completion failure")


def _leaves(error: BaseException) -> tuple[BaseException, ...]:
    if isinstance(error, BaseExceptionGroup):
        return tuple(leaf for child in error.exceptions for leaf in _leaves(child))
    return (error,)


def _assert_pending_cleared(item: object) -> None:
    state = item._y_state
    void = type(item).count.fget.__globals__["VOID"]
    assert state._y_working_tx_ids[0] is None
    assert state._y_count_working is void and state._y_count_staged is void
    assert state._y_untouched_working is void and state._y_untouched_staged is void
    assert state._y_items_working is void and state._y_items_staged is void
    assert state._y_scratch_working is void
    assert state._y_resource_working is void and state._y_resource_staged is void


def _exercise(
    parent_builder: Callable[[type], type], child_builder: Callable[[type], type]
) -> None:
    events: list[str] = []
    controls: dict[str, object] = {"prepare_error": ValueError("conversion failed")}
    parent = parent_builder(_parent_definition(events, controls))
    child = child_builder(_child_definition(parent, events))
    assert issubclass(child, parent)

    def pair() -> tuple[TransactionManager, object, object]:
        events.clear()
        controls.pop("conversion", None)
        manager = TransactionManager(tx_keys=("audit",))
        return (
            manager,
            child(rank=2, control={}, transaction_manager=manager),
            child(rank=1, control={}, transaction_manager=manager),
        )

    for method, phase in (("commit_only", "commit"), ("rollback", "rollback")):
        manager, first, second = pair()
        failure = ValueError(f"first {phase} hook failed")
        first.control[f"{phase}_error"] = failure
        transaction = manager.begin(DEFAULT_TRANSACTION)
        first.count, second.count = 10, 20
        error = _error(lambda: getattr(manager, method)(DEFAULT_TRANSACTION))
        assert error is failure
        for rank in (2, 1):
            assert events.count(f"parent_{phase}:{rank}") == 1
            assert events.count(f"child_{phase}:{rank}") == 1
        assert first.current.count == (10 if phase == "commit" else 0)
        assert second.current.count == (20 if phase == "commit" else 0)
        outcome = transaction.completion
        assert outcome.publication_complete is (phase == "commit")
        assert outcome.discard_complete is (phase == "rollback")
        assert not outcome.after_actions_complete
        assert outcome.finalized and outcome.ownership_preserved
        assert manager.active_transaction is None
        _assert_pending_cleared(first)
        _assert_pending_cleared(second)
        assert any("_parent_after_" in note for note in failure.__notes__)

    manager, first, second = pair()
    parent_error = ValueError("parent after hook failed")
    child_error = KeyboardInterrupt("child after hook interrupted")
    first.control.update(commit_error=parent_error, child_commit_error=child_error)
    transaction = manager.begin(DEFAULT_TRANSACTION)
    first.count, second.count = 10, 20
    error = _error(lambda: manager.commit_only(DEFAULT_TRANSACTION))
    assert isinstance(error, BaseExceptionGroup)
    assert _leaves(error) == (parent_error, child_error)
    assert events[-2:] == ["parent_commit:1", "child_commit:1"]
    assert transaction.completion.publication_complete
    assert not transaction.completion.after_actions_complete
    _assert_pending_cleared(first)
    _assert_pending_cleared(second)

    manager, first, second = pair()
    transaction = manager.begin(DEFAULT_TRANSACTION)
    first.count, second.count = -1, 20
    error = _error(lambda: manager.commit_only(DEFAULT_TRANSACTION))
    assert _leaves(error) == (controls["prepare_error"],)
    assert "before:1" not in events and "freeze:20" not in events
    assert first.current.count == second.current.count == 0
    assert not transaction.completion.publication_started
    assert (
        transaction.completion.discard_complete
        and transaction.completion.after_actions_complete
    )
    _assert_pending_cleared(first)
    _assert_pending_cleared(second)
    # Reuse is exercised only after a clean unpublished discard.
    second.control.clear()
    with manager.begin(DEFAULT_TRANSACTION) as following:
        first.count, second.count = 11, 21
    assert following.completion.publication_complete

    for name in ("count", "untouched", "resource", "scratch"):
        manager, first, second = pair()
        transaction = manager.begin(DEFAULT_TRANSACTION)
        first.count, second.count = 10, 20

        def late_write(item: object) -> None:
            before = getattr(first._y_state, f"_y_{name}_working")
            try:
                setattr(first, name, BindingBase() if name == "resource" else 99)
            except RuntimeError:
                assert getattr(first._y_state, f"_y_{name}_working") is before
                raise

        second.control["before"] = late_write
        error = _error(lambda: manager.commit_only(DEFAULT_TRANSACTION))
        assert isinstance(error, RuntimeError) and "candidate write" in str(error)
        assert not transaction.completion.publication_started
        assert (
            transaction.completion.discard_complete
            and transaction.completion.after_actions_complete
        )
        assert transaction.completion.ownership_preserved
        _assert_pending_cleared(first)
        _assert_pending_cleared(second)

    manager, first, second = pair()
    transaction = manager.begin(DEFAULT_TRANSACTION)
    first.count, second.count = 10, 20

    def permitted_write(item: object) -> None:
        item.count = 11
        second.count = 21

    first.control["before"] = permitted_write
    manager.commit_only(DEFAULT_TRANSACTION)
    assert first.current.count == 11 and second.current.count == 21
    assert (
        transaction.completion.publication_complete
        and transaction.completion.after_actions_complete
    )

    for phase in ("validate", "before", "conversion", "after"):
        for name in ("count", "untouched", "resource", "scratch"):
            manager, first, second = pair()
            transaction = manager.begin(DEFAULT_TRANSACTION)
            first.count, second.count = 10, 20

            def forbidden_write(item: object = first, name: str = name) -> None:
                before = getattr(first._y_state, f"_y_{name}_working")
                try:
                    setattr(first, name, BindingBase() if name == "resource" else 99)
                except RuntimeError:
                    assert getattr(first._y_state, f"_y_{name}_working") is before
                    raise

            if phase == "conversion":
                controls[phase] = forbidden_write
            elif phase == "before":
                second.control[phase] = forbidden_write
            else:
                first.control[phase] = forbidden_write
            error = _error(lambda: manager.commit(DEFAULT_TRANSACTION))
            assert all("candidate write" in str(leaf) for leaf in _leaves(error))
            outcome = transaction.completion
            assert outcome.publication_complete is (phase == "after")
            assert outcome.ownership_preserved and outcome.finalized
            assert first.count == first.current.count == (10 if phase == "after" else 0)
            assert (
                second.count == second.current.count == (20 if phase == "after" else 0)
            )
            _assert_pending_cleared(first)
            _assert_pending_cleared(second)

    manager, first, second = pair()
    outsider = child(rank=0, control={}, transaction_manager=manager)
    transaction = manager.begin(DEFAULT_TRANSACTION)
    first.count, second.count = 10, 20
    first.control["before"] = lambda item: setattr(outsider, "count", 99)
    error = _error(lambda: manager.commit_only(DEFAULT_TRANSACTION))
    assert "candidate write" in str(error)
    assert outsider.count == 0 and outsider._y_state._y_working_tx_ids[0] is None
    assert not transaction.completion.publication_started
    assert transaction.completion.discard_complete

    for failure in (
        ValueError("before hook failed"),
        KeyboardInterrupt("before interrupted"),
    ):
        manager, first, second = pair()
        transaction = manager.begin(DEFAULT_TRANSACTION)
        first.count, second.count = 10, 20

        def fail_before(item: object) -> None:
            raise failure

        first.control["before"] = fail_before
        error = _error(lambda: manager.commit_only(DEFAULT_TRANSACTION))
        assert _leaves(error) == (failure,)
        assert "before:1" not in events and "freeze:10" not in events
        for rank in (2, 1):
            assert events.count(f"parent_rollback:{rank}") == 1
            assert events.count(f"child_rollback:{rank}") == 1
        assert transaction.completion.discard_complete
        assert transaction.completion.after_actions_complete
        assert first.current.count == second.current.count == 0
        _assert_pending_cleared(first)
        _assert_pending_cleared(second)

    for when in ("before_conversion", "after"):
        for name in ("items", "scratch"):
            manager, first, second = pair()
            transaction = manager.begin(DEFAULT_TRANSACTION)
            first.count, second.count = 10, 20
            if when == "after":
                first.control["after"] = lambda item, name=name: getattr(
                    item.working, name
                )
            else:
                controls["conversion"] = lambda name=name: getattr(first.working, name)
            error = _error(lambda: manager.commit_only(DEFAULT_TRANSACTION))
            assert all("candidate write" in str(leaf) for leaf in _leaves(error))
            assert "factory" not in events and "thaw" not in events
            assert transaction.completion.publication_complete is (when == "after")
            assert transaction.completion.ownership_preserved
            _assert_pending_cleared(first)
            _assert_pending_cleared(second)

    manager, first, second = pair()
    other = manager.begin("audit")
    transaction = manager.begin(DEFAULT_TRANSACTION)
    first.count, second.count = 10, 20
    first.control["before"] = lambda item: setattr(item, "audit", 30)
    manager.commit_only(DEFAULT_TRANSACTION)
    assert transaction.completion.publication_complete
    assert manager.active_transaction_for("audit") is other and first.current.audit == 0
    manager.rollback("audit")


def validate_case(sources: Mapping[str, str]) -> None:
    _exercise(
        _builder(sources["generated_parent.py"]),
        _builder(sources["generated_output.py"]),
    )
    _exercise(
        _builder(sources["generated_parent_prettier.py"]),
        _builder(sources["generated_output_prettier.py"]),
    )
    _exercise(lifecycle, lifecycle)
    output = sources["generated_output_prettier.py"]
    assert "_before_commit_hooks(" in output and "_require_candidate_write(" in output
    assert "except BaseException as" in output and "BaseExceptionGroup(" in output
    assert "._parent_after_commit()" in output and "._child_after_commit()" in output


if __name__ == "__main__":
    raise SystemExit(
        run_multi_source_case(
            "yidl_transactional_completion_failures.py", render_case, validate_case
        )
    )
