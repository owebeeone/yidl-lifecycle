from __future__ import annotations

import importlib
import builtins
import ast
import json
import sys

from yidl_lifecycle.bindings import BindingBase
from yidl_cache import DependencyInventory
from yidl_lifecycle.lifecycle import (
    after_commit,
    binding,
    classvar,
    const,
    field,
    initvar,
    lazy,
    lifecycle,
    local_store,
    managed,
    owned,
    transient,
)
from yidl_lifecycle.lifecycle_code_cache import cache_statistics
from yidl_lifecycle.transaction_yidl import TransactionManager


def exercise(value: int, forbid: bool) -> dict[str, int]:
    frontend = importlib.import_module("yidl_lifecycle.lifecycle")
    original = frontend._generate_lifecycle_ast
    calls = 0

    def generate(harvested):
        nonlocal calls
        if forbid:
            raise AssertionError("warm hit attempted generation")
        calls += 1
        return original(harvested)

    frontend._generate_lifecycle_ast = generate
    if forbid:
        compile_original = builtins.compile

        def guarded_compile(source, *args, **kwargs):
            if isinstance(source, ast.AST):
                raise AssertionError("warm hit attempted AST compilation")
            return compile_original(source, *args, **kwargs)

        def no_inventory_recheck(_inventory):
            raise AssertionError("warm hit rechecked generation dependencies")

        builtins.compile = guarded_compile
        DependencyInventory.unchanged = no_inventory_recheck
    events: list[int] = []
    audit_key = object()

    def increment(base: int) -> int:
        return base + value

    def freeze(number: int) -> int:
        return number + value

    def thaw(number: int) -> int:
        return number - value

    class Resource(BindingBase):
        pass

    resource = Resource()

    @lifecycle
    class Parent:
        SCALE: int = classvar(default=value)
        seed: int = initvar(default=value)
        base: int = field(default=value)
        fixed: int = const(default=value)
        computed: int = managed(default_factory=increment)
        converted: int = managed(default=0, thaw=thaw, freeze=freeze)
        scratch: list[int] | None = transient(
            default=None, working_default_factory=lambda seed: [seed]
        )
        deferred: int = lazy(default_factory=lambda base: base + value, mutable=True)
        local: list[int] = local_store(default_factory=lambda base: [base])
        shared: BindingBase | None = binding(default=resource)
        held: BindingBase | None = owned(default=resource)
        audit: int = managed(audit_key, default=0)

        @after_commit()
        def notified(self) -> None:
            events.append(value)

    @lifecycle
    class Child(Parent):
        extra: int = field(default=value + 1)

    manager = TransactionManager(tx_keys=(audit_key,))
    item = Child(transaction_manager=manager)
    assert isinstance(item, Parent)
    assert Child.__yidl_tx_index_to_key__[1] is audit_key
    assert item.base == value and item.extra == value + 1
    assert item.fixed == value and item.SCALE == value
    assert item.computed == value * 2
    assert item.deferred == value * 2 and item.local == [value]
    item.deferred = -1
    assert item.deferred == -1
    assert item.shared is resource and item.held is resource
    with item.begin():
        assert item.scratch == [value]
        item.converted = 3
    assert item.current.converted == value + 3
    assert events == [value]
    try:
        with item.begin():
            item.computed = -99
            raise RuntimeError("discard")
    except RuntimeError:
        pass
    assert item.current.computed == value * 2
    with item.begin(audit_key):
        item.audit = 7
    assert item.current.audit == 7
    assert item.scratch is None
    other = Child(transaction_manager=manager)
    assert other.local is not item.local
    if forbid:
        assert "yidl_lifecycle._generated_lifecycle_base" not in sys.modules
        assert "astichi" not in sys.modules
        assert "yidl.generation.data_def_sys" not in sys.modules
    statistics = cache_statistics()
    assert statistics is not None and statistics.bypasses == 0
    return {
        "generation_calls": calls,
        "hits": statistics.hits,
        "misses": statistics.misses,
        "value": value,
    }


if __name__ == "__main__":
    print(json.dumps(exercise(int(sys.argv[1]), sys.argv[2] == "yes")))
