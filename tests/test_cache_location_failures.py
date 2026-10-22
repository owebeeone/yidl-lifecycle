from __future__ import annotations

import importlib
import builtins
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import ModuleType

import pytest

from yidl_cache import (
    CacheBypass,
    CacheLocationPolicy,
    CacheLocationError,
    DependencyInventory,
    SourceOrigin,
    CacheStorageError,
)
from yidl_lifecycle.lifecycle import field, harvest_lifecycle_definition
from yidl_lifecycle.lifecycle_cache_configuration import OriginResolver


@pytest.mark.parametrize("filename", [False, True])
def test_malformed_spec_uses_plain_file_or_unknown_origin(
    tmp_path, monkeypatch, filename
):
    class BrokenSpec:
        @property
        def origin(self):
            pytest.fail("unsupported spec descriptor was executed")

    module = ModuleType("broken_metadata")
    module.__spec__ = BrokenSpec()
    source = tmp_path / "model.py"
    if filename:
        source.write_text("# source\n")
        module.__file__ = str(source)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    assert OriginResolver(tmp_path).get(module.__name__).path == (
        source if filename else None
    )


@pytest.mark.parametrize("issue", ["metadata", "encoding"])
def test_unusable_origin_does_not_prevent_decorating(tmp_path, issue):
    from importlib.util import find_spec

    roots = [
        str(Path(find_spec(package).origin).resolve().parents[1])
        for package in ("yidl_lifecycle", "yidl_cache", "yidl", "astichi")
    ]
    environment = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join(roots),
        HOME=str(tmp_path),
        YIDL_LIFECYCLE_CACHE="off",
        ASTICHI_LOWER_ENGINE="python",
    )
    script = textwrap.dedent(r"""
        import importlib
        from pathlib import Path
        import sys
        from types import ModuleType
        from yidl_cache import CacheBypass, CacheLocationPolicy, DependencyInventory

        adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
        frontend = importlib.import_module("yidl_lifecycle.lifecycle")
        issue, root = sys.argv[1:]
        module = ModuleType("broken_metadata" if issue == "metadata" else "models\udcff")
        if issue == "metadata":
            class BrokenSpec:
                @property
                def origin(self):
                    raise ValueError("origin unavailable")
            module.__spec__ = BrokenSpec()
        sys.modules[module.__name__] = module
        calls = []
        generate = frontend._generate_lifecycle_ast
        def counted(harvested):
            calls.append(1)
            return generate(harvested)
        frontend._generate_lifecycle_ast = counted
        def definition():
            return type("Example", (), {
                "__module__": module.__name__,
                "__annotations__": {"value": "int"},
                "value": frontend.field(default=1),
            })
        adapter._cache = None
        assert frontend.lifecycle(definition())().value == 1
        dependencies = DependencyInventory.capture({"fixture": Path(adapter.__file__)})
        cache = adapter.LifecycleCodeCache(
            None, dependencies, policy=CacheLocationPolicy(user_root=Path(root) / "home")
        )
        adapter._cache = cache
        assert frontend.lifecycle(definition())().value == 1
        assert calls == [1, 1] and cache.diagnostics[-1].generated
        if issue == "encoding":
            assert cache.statistics.bypasses == 1
            assert cache.diagnostics[-1].outcome is CacheBypass
        print("verified")
        """)
    result = subprocess.run(
        [sys.executable, "-c", script, issue, str(tmp_path)],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "verified"


@pytest.mark.skipif(
    sys.platform not in {"darwin", "linux", "win32"},
    reason="unsupported storage trust platform",
)
def test_fresh_explicit_adapter_clears_prior_artifacts_before_lookup(tmp_path):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    from yidl_cache import CompilationContext

    class Example:
        value: int = field(default=1)

    dependencies = DependencyInventory.capture({"fixture": Path(__file__)})
    compilation = CompilationContext("<test>")
    first = adapter.LifecycleCodeCache(tmp_path / "cache", dependencies)
    first.get(
        harvest_lifecycle_definition(Example),
        compilation,
        lambda: compile("pass", "<test>", "exec", dont_inherit=True),
    )
    leaves = list((tmp_path / "cache").glob("ns-*"))
    unrelated = leaves[0] / "keep.txt"
    unrelated.write_text("keep")
    legacy = tmp_path / "cache" / ("a" * 64 + ".ycode")
    legacy.write_text("legacy")
    neighbor = (
        CacheLocationPolicy(override_root=tmp_path / "cache")
        .locations_for("other-consumer", SourceOrigin(None, ""))[0]
        .directory
    )
    neighbor.mkdir(mode=0o700)
    neighbor_entry = neighbor / ("b" * 64 + ".ycode")
    neighbor_entry.write_text("other")
    automatic = adapter.LifecycleCodeCache(
        None, dependencies, policy=CacheLocationPolicy(user_root=tmp_path / "home")
    )
    assert automatic.clear() == 0
    environment = dict(
        os.environ,
        YIDL_LIFECYCLE_CACHE="on",
        YIDL_LIFECYCLE_CACHE_DIR=str(tmp_path / "cache"),
    )
    roots = []
    from importlib.util import find_spec

    for package in ("yidl_lifecycle", "yidl_cache", "yidl", "astichi"):
        roots.append(str(Path(find_spec(package).origin).resolve().parents[1]))
    environment["PYTHONPATH"] = os.pathsep.join(roots)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from yidl_lifecycle.lifecycle_code_cache import clear_code_cache; print(clear_code_cache())",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "1"
    assert unrelated.read_text() == "keep" and legacy.read_text() == "legacy"
    assert neighbor_entry.read_text() == "other"


@pytest.mark.skipif(
    sys.platform not in {"darwin", "linux"} or os.getuid() == 0,
    reason="requires private-directory access checks as a non-root user",
)
def test_fresh_explicit_clear_reports_inaccessible_ancestor(tmp_path):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    from yidl_cache import CompilationContext

    class Example:
        value: int = field(default=1)

    root = tmp_path / "cache"
    dependencies = DependencyInventory.capture({"fixture": Path(__file__)})
    seeded = adapter.LifecycleCodeCache(root, dependencies)
    seeded.get(
        harvest_lifecycle_definition(Example),
        CompilationContext("<test>"),
        lambda: compile("pass", "<test>", "exec", dont_inherit=True),
    )
    fresh = adapter.LifecycleCodeCache(root, dependencies)
    root.chmod(0)
    try:
        with pytest.raises(CacheLocationError) as caught:
            fresh.clear()
    finally:
        root.chmod(0o700)
    assert len(caught.value.failures) == 1
    assert caught.value.failures[0].problem.kind is CacheStorageError
    assert len(list(root.rglob("*.ycode"))) == 1
    assert fresh.clear() == 1


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS ACL backend")
def test_missing_acl_backend_has_public_lifecycle_failure_snapshot(
    tmp_path, monkeypatch
):
    adapter = importlib.import_module("yidl_lifecycle.lifecycle_code_cache")
    from yidl_cache import CompilationContext

    class Example:
        value: int = field(default=1)

    source = tmp_path / "model.py"
    source.write_text("# source\n")
    module = ModuleType("acl_models")
    module.__file__ = str(source)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    Example.__module__ = module.__name__
    dependencies = DependencyInventory.capture({"fixture": Path(__file__)})
    cache = adapter.LifecycleCodeCache(
        None, dependencies, policy=CacheLocationPolicy(user_root=tmp_path / "home")
    )
    monkeypatch.setattr(adapter, "_cache", cache)
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "ctypes":
            raise ImportError("No module named '_ctypes'")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    compilation = CompilationContext("<test>")
    calls = []
    adapter.compiled_lifecycle_code(
        harvest_lifecycle_definition(Example),
        compilation,
        lambda: calls.append(1) or compile("pass", "<test>", "exec", dont_inherit=True),
    )
    assert calls == [1]
    evidence = adapter.cache_diagnostics()[-1]
    assert evidence.outcome is CacheBypass and evidence.generated
    assert len(evidence.failures) == 2
    assert all(
        failure.problem.kind is CacheStorageError for failure in evidence.failures
    )
    assert adapter.cache_statistics().bypasses == 1
