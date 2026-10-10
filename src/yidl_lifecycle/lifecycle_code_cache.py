"""Default-on compiled-builder reuse, owned by the Lifecycle consumer."""

from __future__ import annotations

from collections.abc import Callable
from importlib.machinery import EXTENSION_SUFFIXES
from importlib.util import find_spec
import os
from pathlib import Path
from types import CodeType

from yidl_cache import (
    CacheBypass,
    CacheDiagnostic,
    CacheDependencyError,
    CacheHit,
    CacheIdentityError,
    CacheMiss,
    CacheLocationPolicy,
    CacheProblem,
    CacheRequest,
    CacheStatistics,
    CompilationContext,
    DependencyInventory,
    GeneratedCodeCache,
    SourceOrigin,
)
from yidl_lifecycle.lifecycle_cache_inputs import generation_digest
from yidl_lifecycle.lifecycle_cache_configuration import (
    CacheConfiguration,
    CacheConfigurationError,
    OriginResolver,
    read_cache_configuration,
)
from yidl_lifecycle.lifecycle_harvester import HarvestedLifecycle

_GENERATOR_REVISION = "lifecycle-builder-v1"
_NAMESPACE = "yidl_lifecycle.builder"


class LifecycleCodeCache:
    def __init__(
        self,
        directory: Path | None,
        dependencies: DependencyInventory | None,
        *,
        policy: CacheLocationPolicy | None = None,
        origins: OriginResolver | None = None,
    ) -> None:
        self._dependencies = dependencies
        self._policy = policy or CacheLocationPolicy(
            override_root=None if directory is None else directory.absolute()
        )
        self._origins = origins or OriginResolver(Path.cwd())
        maintenance = (
            None
            if self._policy.override_root is None
            else self._policy.locations_for(_NAMESPACE, SourceOrigin(None, ""))[
                0
            ].directory
        )
        self._cache = GeneratedCodeCache(maintenance, enabled=True)

    def get(
        self,
        harvested: HarvestedLifecycle,
        compilation: CompilationContext,
        produce: Callable[[], CodeType],
    ) -> CacheHit | CacheMiss | CacheBypass:
        try:
            digest = generation_digest(harvested)
        except CacheIdentityError as error:
            return self._cache.bypass(_NAMESPACE, produce, error)
        request = CacheRequest(
            namespace=_NAMESPACE,
            generator_revision=_GENERATOR_REVISION,
            input_digest=digest,
            compilation=compilation,
            dependencies=self._dependencies,
        )
        module_name = harvested.class_fact["module_name"]
        assert isinstance(module_name, str)
        try:
            locations = self._policy.locations_for(
                _NAMESPACE, self._origins.get(module_name)
            )
        except UnicodeError:
            return self._cache.bypass(
                _NAMESPACE,
                produce,
                CacheIdentityError("unsupported cache location encoding"),
            )
        return self._cache.get(request, produce, locations=locations)

    @property
    def statistics(self) -> CacheStatistics:
        return self._cache.statistics

    @property
    def diagnostics(self) -> tuple[CacheDiagnostic, ...]:
        return self._cache.diagnostics

    def clear(self) -> int:
        return self._cache.clear()


def _dependency_inventory() -> DependencyInventory:
    files: dict[str, Path] = {}
    for name in ("yidl_lifecycle", "yidl", "astichi"):
        spec = find_spec(name)
        if spec is None or not spec.submodule_search_locations:
            raise CacheDependencyError("generation source package is unavailable")
        locations = tuple(spec.submodule_search_locations)
        if len(locations) != 1:
            raise CacheDependencyError("generation package has ambiguous provenance")
        root = Path(locations[0])
        sources = tuple(root.rglob("*.py"))
        if not sources:
            raise CacheDependencyError("generation source files are unavailable")
        for path in sources:
            files[f"{name}/{path.relative_to(root).as_posix()}"] = path
        for path in root.rglob("*"):
            if path.name.endswith(tuple(EXTENSION_SUFFIXES)):
                files[f"{name}/{path.relative_to(root).as_posix()}"] = path
        if name == "astichi":
            # Match Astichi's editable-checkout discovery without importing its engine.
            for parent in root.parents:
                native = parent / "native_engine"
                if (native / "Cargo.toml").is_file():
                    for path in native.glob("_astichi_native_engine*"):
                        if path.name.endswith(tuple(EXTENSION_SUFFIXES)):
                            files[f"astichi/native/{path.name}"] = path
                    break
    spec = find_spec("_astichi_native_engine")
    if spec is not None:
        if not spec.origin:
            raise CacheDependencyError("native extension provenance is unavailable")
        files["astichi/installed-native"] = Path(spec.origin)
    return DependencyInventory.capture(files)


def _startup_configuration() -> tuple[CacheConfiguration, Path | None]:
    try:
        startup = Path.cwd()
    except OSError:
        return (
            CacheConfiguration(
                False,
                problem=CacheProblem(
                    CacheConfigurationError, "startup directory is unavailable"
                ),
            ),
            None,
        )
    home: Path | None
    try:
        home = Path.home()
        if not home.is_absolute():
            home = None
    except (OSError, RuntimeError, ValueError):
        home = None
    return read_cache_configuration(os.environ, startup, home), startup


def _configured_cache(
    configuration: CacheConfiguration, startup: Path | None
) -> LifecycleCodeCache | None:
    if not configuration.enabled:
        return None
    try:
        dependencies = _dependency_inventory()
    except (CacheDependencyError, OSError, ImportError, ValueError):
        dependencies = None
    assert startup is not None
    return LifecycleCodeCache(
        None,
        dependencies,
        policy=CacheLocationPolicy(
            configuration.override_root, configuration.user_root
        ),
        origins=OriginResolver(startup),
    )


# Capture provenance before the first deferred generator import; never relabel it.
_configuration, _startup = _startup_configuration()
_cache = _configured_cache(_configuration, _startup)


def compiled_lifecycle_code(
    harvested: HarvestedLifecycle,
    compilation: CompilationContext,
    produce: Callable[[], CodeType],
) -> CodeType:
    if _cache is None:
        return produce()
    return _cache.get(harvested, compilation, produce).code


def cache_statistics() -> CacheStatistics | None:
    """No logging by default; return counters only when explicitly requested."""
    return None if _cache is None else _cache.statistics


def cache_configuration() -> CacheConfiguration:
    """Frozen startup settings; this performs no I/O and reads no application YAML."""
    return _configuration


def cache_diagnostics() -> tuple[CacheDiagnostic, ...]:
    """The most recent 32 completed cache requests, without retained tracebacks."""
    return () if _cache is None else _cache.diagnostics


def clear_code_cache() -> int:
    """Explicit maintenance. Restart after generator edits or configuration changes."""
    return 0 if _cache is None else _cache.clear()
