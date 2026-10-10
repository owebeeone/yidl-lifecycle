from __future__ import annotations

from dataclasses import replace
import importlib
from importlib.util import find_spec
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from yidl_cache import (
    CacheBypass,
    CacheIdentityError,
    CompilationContext,
    DependencyInventory,
    CacheHit,
    CacheLocationPolicy,
    CacheStorageError,
)
from yidl_lifecycle.lifecycle import after_commit, field, harvest_lifecycle_definition
from yidl_lifecycle.lifecycle import managed
from yidl_lifecycle.lifecycle_cache_inputs import generation_digest


def definition(key: object = "audit", other_key: object = "audit"):
    class Example:
        value: int = field(default=1)
        derived: int = managed(default_factory=lambda value: value + 1)
        audit: int = managed(key, default=0)
        other: int = managed(other_key, default=0)

        @after_commit(key)
        def notify(self) -> None:
            pass

    return harvest_lifecycle_definition(Example)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("field_order", 99),
        ("field_kind", "const"),
        ("annotation", "float"),
        ("default_factory_param_names", ("audit",)),
        ("compare", "identity"),
        ("mutable", True),
        ("has_optional_none", True),
        ("current_slot_name", "_y_other_current"),
        ("init", False),
    ],
)
def test_generation_relevant_field_changes_have_distinct_fingerprints(name, value):
    harvested = definition()
    facts = list(harvested.field_facts)
    facts[0] = dict(facts[0], **{name: value})
    changed = replace(harvested, field_facts=tuple(facts))
    assert generation_digest(changed) != generation_digest(harvested)


def test_name_and_hook_order_are_generation_inputs():
    harvested = definition()
    changed = replace(
        harvested, class_fact=dict(harvested.class_fact, module_name="new")
    )
    assert generation_digest(changed) != generation_digest(harvested)
    method = dict(harvested.transaction_method_facts[0], declaration_order=99)
    changed = replace(harvested, transaction_method_facts=(method,))
    assert generation_digest(changed) != generation_digest(harvested)


def test_key_topology_not_key_object_identity_is_fingerprinted():
    first = object()
    second = object()
    assert generation_digest(definition(first, first)) == generation_digest(
        definition(second, second)
    )
    assert generation_digest(definition(first, first)) != generation_digest(
        definition(first, second)
    )


@pytest.mark.parametrize("location", ["class", "field", "method"])
def test_unknown_fact_schema_is_not_cacheable(location):
    harvested = definition()
    if location == "class":
        changed = replace(
            harvested, class_fact=dict(harvested.class_fact, new_flag=True)
        )
    elif location == "field":
        facts = list(harvested.field_facts)
        facts[0] = dict(facts[0], new_flag=True)
        changed = replace(harvested, field_facts=tuple(facts))
    else:
        method = dict(harvested.transaction_method_facts[0], new_flag=True)
        changed = replace(harvested, transaction_method_facts=(method,))
    with pytest.raises(CacheIdentityError, match="schema"):
        generation_digest(changed)


def test_live_annotation_is_not_encoded_using_repr():
    harvested = definition()
    facts = list(harvested.field_facts)
    facts[0] = dict(facts[0], annotation=int)
    with pytest.raises(CacheIdentityError, match="annotation"):
        generation_digest(replace(harvested, field_facts=tuple(facts)))


@pytest.mark.skipif(
    sys.platform not in {"darwin", "linux"},
    reason="persistent trust checks require macOS/Linux",
)
@pytest.mark.parametrize("placement", ["override", "local", "home"])
def test_canonical_lifecycle_fixture_reuses_code_in_fresh_processes(
    tmp_path, placement
):
    fixture = Path(__file__).parent / "data" / "cache" / "lifecycle_process.py"
    environment = dict(os.environ, HOME=str(tmp_path / "home"))
    environment.pop("YIDL_LIFECYCLE_CACHE", None)
    environment.pop("YIDL_LIFECYCLE_CACHE_DIR", None)
    source = tmp_path / "source"
    source.mkdir()
    copied = source / fixture.name
    copied.write_bytes(fixture.read_bytes())
    fixture = copied
    if placement == "override":
        environment["YIDL_LIFECYCLE_CACHE_DIR"] = str(tmp_path / "cache")
    elif placement == "home":
        blocked = source / "__pycache__"
        blocked.mkdir()
        (blocked / "yidl_cache").write_text(
            "local storage unavailable", encoding="utf-8"
        )
    roots = []
    for package in ("yidl_lifecycle", "yidl_cache", "yidl", "astichi"):
        spec = find_spec(package)
        assert spec is not None and spec.origin is not None
        roots.append(str(Path(spec.origin).resolve().parents[1]))
    environment["PYTHONPATH"] = os.pathsep.join(roots)

    def run(value: int, forbid: bool):
        completed = subprocess.run(
            [sys.executable, str(fixture), str(value), "yes" if forbid else "no"],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout)

    cold = run(10, False)
    warm = run(90, True)
    assert cold == {"generation_calls": 2, "hits": 0, "misses": 2, "value": 10}
    assert warm == {"generation_calls": 0, "hits": 2, "misses": 0, "value": 90}
    directory = (
        source / "__pycache__" / "yidl_cache"
        if placement == "local"
        else (
            tmp_path / "cache"
            if placement == "override"
            else tmp_path / "home" / ".yidl" / "cache"
        )
    )
    assert len(list(directory.rglob("*.ycode"))) == 2


def test_opt_in_adapter_preserves_failure_diagnostics_and_validation(
    tmp_path, monkeypatch
):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    frontend = importlib.import_module("yidl_lifecycle.lifecycle")
    monkeypatch.setattr(adapter, "_cache", adapter.LifecycleCodeCache(tmp_path, None))

    class Broken:
        value: int = field(default=0)

    def fail(_harvested):
        raise ValueError("producer broke")

    monkeypatch.setattr(frontend, "_generate_lifecycle_ast", fail)
    with pytest.raises(
        frontend.LifecycleDefinitionError,
        match="Broken: lifecycle AST generation failed",
    ):
        frontend.lifecycle(Broken)

    class Invalid:
        _y_reserved: int

    with pytest.raises(frontend.LifecycleDefinitionError, match="reserved"):
        frontend.lifecycle(Invalid)


def test_unknown_annotation_bypasses_without_inspecting_user_objects(tmp_path):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    cache = adapter.LifecycleCodeCache(tmp_path, None)
    harvested = definition()
    facts = list(harvested.field_facts)
    facts[0] = dict(facts[0], annotation=int)
    compilation = CompilationContext("<test>")
    code = compile("pass", compilation.filename, "exec", dont_inherit=True)
    result = cache.get(
        replace(harvested, field_facts=tuple(facts)), compilation, lambda: code
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheIdentityError)
    assert result.code is code
    assert cache.statistics.bypasses == 1
    assert not list(tmp_path.glob("*.ycode"))


@pytest.mark.parametrize("step", ["AST execution", "class build"])
@pytest.mark.skipif(
    sys.platform not in {"darwin", "linux"},
    reason="persistent trust checks require macOS/Linux",
)
def test_cached_execution_and_binding_failures_keep_class_context(
    tmp_path, monkeypatch, step
):
    import ast

    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    frontend = importlib.import_module("yidl_lifecycle.lifecycle")
    inventory = DependencyInventory.capture({"fixture": Path(__file__)})
    cache = adapter.LifecycleCodeCache(tmp_path / "cache", inventory)
    monkeypatch.setattr(adapter, "_cache", cache)

    class Broken:
        value: int = field(default=0)

    if step == "AST execution":
        source = "raise ValueError('execution failed')"
    else:
        source = "def build_lifecycle_class(*args, **kwargs):\n    raise ValueError('binding failed')\n"
    monkeypatch.setattr(
        frontend, "_generate_lifecycle_ast", lambda _: ast.parse(source)
    )
    with pytest.raises(
        frontend.LifecycleDefinitionError, match=f"Broken: lifecycle {step} failed"
    ):
        frontend.lifecycle(Broken)
    monkeypatch.setattr(
        frontend,
        "_generate_lifecycle_ast",
        lambda _: pytest.fail("unexpected generation"),
    )
    with pytest.raises(
        frontend.LifecycleDefinitionError, match=f"Broken: lifecycle {step} failed"
    ):
        frontend.lifecycle(Broken)
    assert cache.statistics.hits == 1


def test_invalid_factory_dependencies_still_fail_with_caching(tmp_path, monkeypatch):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    frontend = importlib.import_module("yidl_lifecycle.lifecycle")
    inventory = DependencyInventory.capture({"fixture": Path(__file__)})
    monkeypatch.setattr(
        adapter, "_cache", adapter.LifecycleCodeCache(tmp_path / "cache", inventory)
    )

    class Invalid:
        value: int = managed(default_factory=lambda unknown_provider: unknown_provider)

    for _ in range(2):
        with pytest.raises(frontend.LifecycleDefinitionError, match="unknown_provider"):
            frontend.lifecycle(Invalid)
    assert not list((tmp_path / "cache").glob("*.ycode"))


@pytest.mark.skipif(
    sys.platform not in {"darwin", "linux"},
    reason="persistent trust checks require macOS/Linux",
)
def test_relative_cache_directory_is_fixed_before_working_directory_changes(
    tmp_path, monkeypatch
):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    inventory = DependencyInventory.capture({"fixture": Path(__file__).resolve()})
    monkeypatch.chdir(tmp_path)
    cache = adapter.LifecycleCodeCache(Path("cache"), inventory)
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    compilation = CompilationContext("<test>")
    code = compile("pass", compilation.filename, "exec", dont_inherit=True)
    cache.get(definition(), compilation, lambda: code)
    assert (tmp_path / "cache").is_dir()
    assert not (other / "cache").exists()


def test_public_diagnostics_expose_failed_publication_and_exhausted_routes(
    tmp_path, monkeypatch, capsys
):
    from types import ModuleType
    from yidl_cache.storage import ArtifactStorage
    from yidl_lifecycle.lifecycle_cache_configuration import OriginResolver

    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    source = tmp_path / "models.py"
    source.write_text("# source\n", encoding="utf-8")
    module = ModuleType("synthetic_models")
    module.__file__ = str(source)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    harvested = definition()
    harvested = replace(
        harvested, class_fact=dict(harvested.class_fact, module_name=module.__name__)
    )
    inventory = DependencyInventory.capture({"fixture": source})
    compilation = CompilationContext("<test>")
    code = compile("pass", compilation.filename, "exec", dont_inherit=True)
    policy = CacheLocationPolicy(user_root=tmp_path / "home")
    origins = OriginResolver(tmp_path)
    local = policy.locations_for(
        "yidl_lifecycle.builder", origins.get(module.__name__)
    )[0]
    original = ArtifactStorage.write
    calls = []

    def produce():
        calls.append(1)
        return code

    def fail_local(self, *args):
        if self.directory == local.directory:
            raise CacheStorageError("local publication failed")
        return original(self, *args)

    monkeypatch.setattr(ArtifactStorage, "write", fail_local)

    def install():
        monkeypatch.setattr(
            adapter,
            "_cache",
            adapter.LifecycleCodeCache(None, inventory, policy=policy, origins=origins),
        )

    install()
    adapter.compiled_lifecycle_code(harvested, compilation, produce)
    install()
    assert adapter.compiled_lifecycle_code(harvested, compilation, produce) is not None
    evidence = adapter.cache_diagnostics()[-1]
    assert evidence.outcome is CacheHit and evidence.generated
    assert len(evidence.attempted) == 2 and len(evidence.failures) == 1
    assert evidence.failures[0].problem.kind is CacheStorageError
    assert calls == [1, 1]
    assert adapter.cache_statistics().hits == 1

    def fail_admission(self):
        raise CacheStorageError("cannot admit location")

    monkeypatch.setattr(ArtifactStorage, "admit", fail_admission)
    install()
    for _ in range(40):
        assert adapter.compiled_lifecycle_code(harvested, compilation, produce) is code
    evidence = adapter.cache_diagnostics()[-1]
    assert evidence.outcome is CacheBypass and evidence.generated
    assert len(evidence.failures) == 2
    assert len(adapter.cache_diagnostics()) == 32
    assert adapter.cache_statistics().bypasses == 40
    assert capsys.readouterr() == ("", "")


def test_explicit_off_does_not_inventory_or_create_directories(tmp_path):
    roots = []
    for package in ("yidl_lifecycle", "yidl_cache", "yidl", "astichi"):
        spec = find_spec(package)
        roots.append(str(Path(spec.origin).resolve().parents[1]))
    script = """
from yidl_cache import DependencyInventory
def fail(*args, **kwargs):
    raise AssertionError('disabled cache captured provenance')
DependencyInventory.capture = fail
from yidl_lifecycle.lifecycle_code_cache import cache_configuration, cache_statistics, cache_diagnostics
assert not cache_configuration().enabled
assert cache_statistics() is None and cache_diagnostics() == ()
"""
    directory = tmp_path / "unused"
    environment = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join(roots),
        YIDL_LIFECYCLE_CACHE="off",
        YIDL_LIFECYCLE_CACHE_DIR=str(directory),
    )
    result = subprocess.run(
        [sys.executable, "-c", script], env=environment, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert not directory.exists()
