"""Live annotation boundaries; deliberately no future-annotations import."""

import importlib
import inspect
import marshal
from types import MappingProxyType

import pytest

from yidl_lifecycle.bindings import BindingBase
from yidl_cache import CacheBypass, CompilationContext
from yidl_lifecycle.lifecycle import (
    _generate_lifecycle_ast,
    harvest_lifecycle_definition,
)
from yidl_lifecycle.lifecycle import binding
from yidl_lifecycle.lifecycle_code_cache import LifecycleCodeCache
from yidl_lifecycle.lifecycle import const, field, initvar, lazy, lifecycle, managed
from yidl_lifecycle.lifecycle import owned, transient


@pytest.fixture(autouse=True)
def disable_persistent_cache(monkeypatch):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    monkeypatch.setattr(adapter, "_cache", None)


def test_harvester_reads_local_runtime_annotations():
    class Payload:
        pass

    class Base:
        inherited_only: "Unresolved"

    class Config(Base):
        value: Payload = field()

    harvested = harvest_lifecycle_definition(Config)
    assert dict(harvested.annotations) == {"value": Payload}
    assert [fact["field_name"] for fact in harvested.field_facts] == ["value"]
    assert not harvest_lifecycle_definition(type("Empty", (Config,), {})).field_facts


def test_harvester_preserves_explicit_annotation_mappings():
    class Config:
        __annotations__ = MappingProxyType({"value": "Unresolved"})
        value = field()

    harvested = harvest_lifecycle_definition(Config)
    assert dict(harvested.annotations) == {"value": "Unresolved"}


@pytest.mark.parametrize(
    "marker", [field, initvar, const, managed, transient, owned, binding]
)
@pytest.mark.parametrize("mode", ["required", "default", "factory"])
def test_constructor_preserves_live_annotation_and_value_identity(marker, mode):
    class Payload(BindingBase):
        pass

    default = Payload()
    calls = []

    def factory():
        calls.append(True)
        return default

    kwargs = {
        "required": {},
        "default": {"default": default},
        "factory": {"default_factory": factory},
    }[mode]

    class Config:
        storage_anchor: int = field(default=0, init=False)
        value: Payload = marker(**kwargs)

    generated = lifecycle(Config)
    parameter = inspect.signature(generated).parameters["value"]
    assert "storage_anchor" not in inspect.signature(generated).parameters
    assert parameter.annotation is Payload
    assert generated.__annotations__["value"] is Payload
    if mode == "required":
        instance = generated(default)
    else:
        instance = generated()
    if marker is not initvar:
        assert instance.value is default
    assert calls == ([True] if mode == "factory" else [])
    if mode == "default":
        assert parameter.default is default


def test_mutable_lazy_with_runtime_int_annotation():
    @lifecycle
    class Config:
        seed: int = lazy(default=2, mutable=True)

    assert Config().seed == 2
    assert inspect.signature(Config).parameters["seed"].annotation is int


def test_live_annotations_bypass_cache_and_rebind_after_code_roundtrip(tmp_path):
    def make(annotation):
        class Config:
            __annotations__ = {"value": annotation}
            value = field()

        return Config, harvest_lifecycle_definition(Config)

    first_type = type("Payload", (), {})
    second_type = type("Payload", (), {})
    first_cls, first = make(first_type)
    second_cls, second = make(second_type)
    cache = LifecycleCodeCache(tmp_path, None)
    context = CompilationContext("<annotation-regression>")

    def produce():
        return compile(
            _generate_lifecycle_ast(first),
            context.filename,
            "exec",
            dont_inherit=True,
        )

    result = cache.get(first, context, produce)
    assert isinstance(result, CacheBypass)
    assert "annotation" in str(result.reason)
    assert not list(tmp_path.rglob("*.ycode"))

    namespace = {"__name__": __name__}
    exec(marshal.loads(marshal.dumps(result.code)), namespace)
    build = namespace["build_lifecycle_class"]
    first_generated = build(first_cls, **first.build_kwargs)
    second_generated = build(second_cls, **second.build_kwargs)
    assert (
        inspect.signature(first_generated).parameters["value"].annotation is first_type
    )
    assert (
        inspect.signature(second_generated).parameters["value"].annotation
        is second_type
    )


def test_inherited_constructor_annotations_include_overrides_and_initvars():
    class Original:
        pass

    class Replacement:
        pass

    @lifecycle
    class Base:
        value: Original = field()
        seed: Original = initvar()
        unchanged: Original = field()

    @lifecycle
    class Derived(Base):
        value: Replacement = field()

    parameters = inspect.signature(Derived).parameters
    assert parameters["value"].annotation is Replacement
    assert parameters["seed"].annotation is Original
    assert parameters["unchanged"].annotation is Original
    assert dict(Derived.__annotations__) == {"value": Replacement}


@pytest.mark.parametrize("postponed", [False, True])
def test_string_annotations_remain_strings(postponed):
    source = (
        ("from __future__ import annotations\n" if postponed else "")
        + "class Config:\n"
        + (
            "    value: Payload = field()\n"
            if postponed
            else "    value: 'Payload' = field()\n"
        )
    )
    namespace = {"field": field, "__name__": __name__}
    exec(
        compile(source, "<annotation-regression>", "exec", dont_inherit=True), namespace
    )
    generated = lifecycle(namespace["Config"])
    assert inspect.signature(generated).parameters["value"].annotation == "Payload"
    assert generated.__annotations__["value"] == "Payload"
