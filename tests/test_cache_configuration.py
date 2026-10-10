from __future__ import annotations

from pathlib import Path
import sys
from types import ModuleType
from importlib.machinery import ModuleSpec

import pytest

from yidl_lifecycle.lifecycle_cache_configuration import (
    CacheConfigurationError,
    OriginResolver,
    read_cache_configuration,
)


@pytest.mark.parametrize(
    ("enable", "directory", "enabled", "override"),
    [
        (None, None, True, False),
        ("", "", True, False),
        (" on ", None, True, False),
        ("OFF", "cache", False, False),
        (None, "cache", True, True),
        ("on", "cache", True, True),
    ],
)
def test_configuration_precedence(tmp_path, enable, directory, enabled, override):
    environ = {}
    if enable is not None:
        environ["YIDL_LIFECYCLE_CACHE"] = enable
    if directory is not None:
        environ["YIDL_LIFECYCLE_CACHE_DIR"] = directory
    configuration = read_cache_configuration(environ, tmp_path, tmp_path / "home")
    assert configuration.enabled is enabled
    assert (configuration.override_root is not None) is override
    if override:
        assert configuration.override_root == tmp_path / "cache"
    assert configuration.problem is None
    assert not (tmp_path / "home").exists()


@pytest.mark.parametrize("directory", ["~/cache", "a/../cache", " cache "])
def test_paths_are_expanded_lexically_not_symlink_resolved(tmp_path, directory):
    configuration = read_cache_configuration(
        {"YIDL_LIFECYCLE_CACHE_DIR": directory}, tmp_path, tmp_path / "home"
    )
    expected = {
        "~/cache": tmp_path / "home" / "cache",
        "a/../cache": tmp_path / "cache",
        " cache ": tmp_path / " cache ",
    }
    assert configuration.override_root == expected[directory]


@pytest.mark.parametrize(
    "environ",
    [
        {"YIDL_LIFECYCLE_CACHE": "false"},
        {"YIDL_LIFECYCLE_CACHE_DIR": "~other/cache"},
        {"YIDL_LIFECYCLE_CACHE_DIR": "~/cache"},
    ],
)
def test_invalid_configuration_disables_without_import_failure(tmp_path, environ):
    configuration = read_cache_configuration(environ, tmp_path, None)
    assert not configuration.enabled
    assert configuration.problem.kind is CacheConfigurationError


def test_symlinked_author_origin_resolves_but_module_lookup_retains_no_modules(
    tmp_path, monkeypatch
):
    source = tmp_path / "actual.py"
    source.write_text("# author\n", encoding="utf-8")
    link = tmp_path / "link.py"
    link.symlink_to(source)
    module = ModuleType("models")
    module.__spec__ = ModuleSpec("models", None, origin=str(link))
    monkeypatch.setitem(sys.modules, "models", module)
    resolver = OriginResolver(tmp_path)
    assert resolver.get("models").path == source.resolve()
    for index in range(40):
        assert resolver.get(f"unknown_{index}").path is None
    assert len(resolver._origins) == 32


def test_relative_origin_is_fixed_at_startup_and_archives_are_unknown(
    tmp_path, monkeypatch
):
    source = tmp_path / "model.py"
    source.write_text("# author\n", encoding="utf-8")
    module = ModuleType("models")
    module.__file__ = "model.py"
    monkeypatch.setitem(sys.modules, "models", module)
    resolver = OriginResolver(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    assert resolver.get("models").path == source.resolve()
    module.__file__ = "archive.zip/model.py"
    assert resolver.get("models").path is None
