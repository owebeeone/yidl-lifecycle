"""Consumer settings and bounded source-origin metadata, without generator imports."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.machinery import ModuleSpec
import os
from pathlib import Path
import sys
from threading import Lock
from types import ModuleType

from yidl_cache.locations import SourceOrigin
from yidl_cache.model import CacheError
from yidl_cache.diagnostics import CacheProblem


class CacheConfigurationError(CacheError):
    """Cache settings could not be interpreted safely."""


@dataclass(frozen=True)
class CacheConfiguration:
    enabled: bool
    override_root: Path | None = None
    user_root: Path | None = None
    problem: CacheProblem | None = None


def read_cache_configuration(
    environment: Mapping[str, str], startup_directory: Path, home: Path | None
) -> CacheConfiguration:
    setting = environment.get("YIDL_LIFECYCLE_CACHE", "").strip().lower()
    if setting == "off":
        return CacheConfiguration(False)
    if setting not in {"", "on"}:
        return _invalid("YIDL_LIFECYCLE_CACHE must be on or off")
    directory = environment.get("YIDL_LIFECYCLE_CACHE_DIR", "")
    try:
        if directory.startswith("~"):
            if directory != "~" and not directory.startswith("~/"):
                return _invalid("only current-user ~ expansion is supported")
            if home is None:
                return _invalid("cannot expand cache root without a home directory")
            directory = str(home / directory[2:]) if directory != "~" else str(home)
        override = None
        if directory:
            if "\x00" in directory:
                return _invalid("cache root contains a null character")
            path = Path(directory)
            if not path.is_absolute():
                path = startup_directory / path
            override = Path(os.path.normpath(path))
        user_root = None if home is None else home / ".yidl" / "cache"
        return CacheConfiguration(True, override, user_root)
    except (OSError, ValueError, RuntimeError):
        return _invalid("cannot normalize cache configuration")


def _invalid(message: str) -> CacheConfiguration:
    return CacheConfiguration(
        False, problem=CacheProblem(CacheConfigurationError, message)
    )


class OriginResolver:
    def __init__(self, startup_directory: Path) -> None:
        self._startup_directory = startup_directory
        self._origins: OrderedDict[tuple[str, str | None, str | None], SourceOrigin] = (
            OrderedDict()
        )
        self._lock = Lock()

    def get(self, module_name: str) -> SourceOrigin:
        module = sys.modules.get(module_name)
        attributes = vars(module) if type(module) is ModuleType else {}
        spec = attributes.get("__spec__")
        origin = vars(spec).get("origin") if type(spec) is ModuleSpec else None
        filename = attributes.get("__file__")
        origin = origin if type(origin) is str else None
        filename = filename if type(filename) is str else None
        key = (module_name, origin, filename)
        with self._lock:
            existing = self._origins.get(key)
            if existing is not None:
                self._origins.move_to_end(key)
                return existing
        result = SourceOrigin(self._path(origin) or self._path(filename), module_name)
        with self._lock:
            self._origins[key] = result
            self._origins.move_to_end(key)
            while len(self._origins) > 32:
                self._origins.popitem(last=False)
        return result

    def _path(self, value: str | None) -> Path | None:
        if value is None:
            return None
        try:
            path = Path(value)
            if path.suffix.lower() not in {".py", ".pyw"}:
                return None
            if not path.is_absolute():
                path = self._startup_directory / path
            resolved = path.resolve(strict=True)
            str(resolved).encode("utf-8")
            return resolved if resolved.is_file() else None
        except (OSError, ValueError, RuntimeError, UnicodeError):
            return None
