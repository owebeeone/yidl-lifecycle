from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path

import black

from support.golden_case import run_multi_source_case
from yidl_lifecycle.lifecycle import _generate_lifecycle_source
from yidl_lifecycle.lifecycle import const
from yidl_lifecycle.lifecycle import harvest_lifecycle_definition
from yidl_lifecycle.lifecycle import initvar
from yidl_lifecycle.lifecycle import lazy
from yidl_lifecycle.lifecycle import lifecycle
from yidl_lifecycle.lifecycle import static

DECORATOR_PATH = Path("src/yidl_lifecycle/_generated_lifecycle_base.py")


def render_case() -> Mapping[str, str]:
    decorator_source = DECORATOR_PATH.read_text(encoding="utf-8")
    output_source = _generate_lifecycle_source(
        harvest_lifecycle_definition(_fixture_class()),
    )
    return {
        "decorator.py": decorator_source,
        "decorator_prettier.py": _prettier_source(decorator_source),
        "generated_output.py": output_source,
        "generated_output_prettier.py": _prettier_source(output_source),
    }


def validate_case(sources: Mapping[str, str]) -> None:
    decorator_namespace: dict[str, object] = {}
    exec(sources["decorator.py"], decorator_namespace)
    assert "ConstField" in decorator_namespace
    assert "StaticField" in decorator_namespace
    assert "build_LifecycleModule" in decorator_namespace

    output_namespace: dict[str, object] = {}
    exec(sources["generated_output.py"], output_namespace)
    output_prettier_namespace: dict[str, object] = {}
    exec(sources["generated_output_prettier.py"], output_prettier_namespace)

    _assert_generated_class(output_namespace)
    _assert_generated_class(output_prettier_namespace)
    _assert_decorator_frontend()
    _assert_source_shape(sources)


def _fixture_class() -> type[object]:
    calls: list[None] = []
    mutable_calls: list[int] = []

    def make_items() -> list[int]:
        calls.append(None)
        return [1, 2]

    def make_mutable_items(mutable_number: int) -> list[int]:
        mutable_calls.append(mutable_number)
        return [mutable_number]

    class Config:
        seed: int = initvar(default=3)
        slot_id: int = const(default=7)
        derived_id: int = const(default_factory=lambda seed, slot_id: seed + slot_id)
        declared: tuple[str, ...] = lazy()
        lazy_number: int = lazy(default=42)
        items: list[int] = lazy(default_factory=make_items)
        seeded_static: int = static(default_factory=lambda slot_id: slot_id + 5)
        mutable_unset: int = lazy(mutable=True)
        mutable_number: int = lazy(default=42, mutable=True)
        mutable_items: list[int] = lazy(
            default_factory=make_mutable_items,
            mutable=True,
        )
        mutable_no_init: int = static(
            default_factory=lambda mutable_number: mutable_number + 1,
            init=False,
            mutable=True,
        )

    Config._test_factory_calls = calls
    Config._test_mutable_factory_calls = mutable_calls
    return Config


def _assert_generated_class(namespace: Mapping[str, object]) -> None:
    config_cls = _fixture_class()
    harvested = harvest_lifecycle_definition(config_cls)
    generated = namespace["build_lifecycle_class"](
        config_cls,
        **dict(harvested.build_kwargs),
    )
    _assert_config_class(generated)


def _assert_decorator_frontend() -> None:
    generated = lifecycle(_fixture_class())
    _assert_config_class(generated)

    @lifecycle
    class Child(generated):
        lazy_number: int = lazy(default=43, mutable=True)

    child = Child()
    assert child.lazy_number == 43
    child.lazy_number = 44
    child.lazy_number = 45
    assert child.lazy_number == 45
    child.mutable_number = 10
    child.mutable_number = 20
    assert child.mutable_items == [20]


def _assert_config_class(generated: type[object]) -> None:
    item = generated()

    assert item.slot_id == 7
    assert item.current.slot_id == 7
    assert item.working.slot_id == 7
    assert item.derived_id == 10
    _assert_raises(
        AttributeError,
        "const field 'slot_id' is read-only",
        lambda: setattr(item, "slot_id", 8),
    )
    _assert_raises(
        AttributeError,
        "const field 'slot_id' is read-only",
        lambda: setattr(item.current, "slot_id", 8),
    )

    _assert_raises(
        AttributeError,
        "static field 'declared' is not initialized",
        lambda: getattr(item, "declared"),
    )
    item.declared = ("a", "b")
    assert item.declared == ("a", "b")
    assert item.current.declared == ("a", "b")
    assert item.working.declared == ("a", "b")
    _assert_raises(
        AttributeError,
        "static field 'declared' is already initialized",
        lambda: setattr(item, "declared", ("x",)),
    )

    override = generated(lazy_number=7)
    assert override.lazy_number == 7
    assign_first = generated()
    assign_first.lazy_number = 9
    assert assign_first.lazy_number == 9
    read_default = generated()
    assert read_default.lazy_number == 42

    calls = getattr(generated.__yidl_lifecycle_user_class__, "_test_factory_calls")
    assert calls == []
    assert item.items == [1, 2]
    assert calls == [None]
    assert item.items is item.items
    assert item.seeded_static == 12

    mutable_calls = getattr(
        generated.__yidl_lifecycle_user_class__, "_test_mutable_factory_calls"
    )
    assert mutable_calls == []
    _assert_raises(
        AttributeError,
        "static field 'mutable_unset' is not initialized",
        lambda: getattr(item, "mutable_unset"),
    )
    item.mutable_unset = 1
    item.mutable_unset = 2
    assert item.mutable_unset == 2

    assert item.mutable_number == 42
    item.mutable_number = 10
    item.current.mutable_number = 11
    item.working.mutable_number = 12
    assert item.mutable_number == item.current.mutable_number == 12

    constructor_value = generated(mutable_items=[5])
    assert constructor_value.mutable_items == [5]
    assignment_first = generated()
    assignment_first.mutable_items = [6]
    assignment_first.mutable_items = [7]
    assert assignment_first.mutable_items == [7]
    assert mutable_calls == []

    assert item.mutable_items == [12]
    assert mutable_calls == [12]
    item.mutable_number = 13
    assert item.mutable_items == [12]
    item.current.mutable_items = [14]
    item.working.mutable_items = [15]
    assert item.mutable_items == [15]
    assert mutable_calls == [12]

    assert item.mutable_no_init == 14
    item.mutable_no_init = 16
    item.mutable_no_init = 17
    assert item.mutable_no_init == 17

    manager = item._y_get_transaction_manager()
    manager.begin()
    item.mutable_number = 18
    manager.rollback()
    assert item.mutable_number == 18


def _assert_raises(
    exception_type: type[BaseException],
    message: str,
    func: object,
) -> None:
    try:
        func()
    except exception_type as exc:
        assert message in str(exc)
        return
    raise AssertionError(f"expected {exception_type.__name__}")


def _assert_source_shape(sources: Mapping[str, str]) -> None:
    source = sources["generated_output.py"]
    prettier_source = sources["generated_output_prettier.py"]
    for generated in (source, prettier_source):
        assert "const field {'slot_id'!r} is read-only" in generated
        assert "static field {'declared'!r} is not initialized" in generated
        assert "static field {'declared'!r} is already initialized" in generated
        assert "_y_declared_value = VOID" in generated
        assert "_Config_items_default_factory()" in generated
        assert (
            "_Config_seeded_static_default_factory(slot_id=self.slot_id)" in generated
        )
        facade = next(
            node
            for node in ast.walk(ast.parse(generated))
            if isinstance(node, ast.ClassDef) and node.name == "Config_FacadeBase"
        )
        setters = {
            node.name: node
            for node in facade.body
            if isinstance(node, ast.FunctionDef)
            and any(
                isinstance(decorator, ast.Attribute) and decorator.attr == "setter"
                for decorator in node.decorator_list
            )
        }
        assert any(isinstance(node, ast.Raise) for node in ast.walk(setters["items"]))
        for name in (
            "mutable_unset",
            "mutable_number",
            "mutable_items",
            "mutable_no_init",
        ):
            assert not any(
                isinstance(node, ast.If | ast.Raise) for node in ast.walk(setters[name])
            )


def _prettier_source(source: str) -> str:
    return black.format_str(source, mode=black.FileMode())


if __name__ == "__main__":
    raise SystemExit(
        run_multi_source_case(
            "yidl_transactional_parity_fields1.py",
            render_case,
            validate_case,
        )
    )
