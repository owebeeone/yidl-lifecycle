# Lifecycle contributors and internals

For using the package, start at the [public documentation](../docs/index.md).
This page retains implementation and release information outside the user
learning route.

## Generated builders and dependencies

Lifecycle ships a committed generated base in its wheel and source distribution;
installation does not regenerate it. The handwritten public decorator uses that
base to build decorated classes. YIDL is both a runtime dependency and the
compiler used for regeneration. The generated base imports YIDL record/container
primitives, assembly plans and execution, and Astichi template adapters. Field
markers use module-owned compat-sentinel sentinels.

Lifecycle pins the exact published YIDL version used to regenerate and qualify
its shipped builders. A different version requires regeneration, compatibility
checks and a corresponding release. Astichi compatibility also requires
qualification; it is not automatically interchangeable. Version 0.1.1 pins
Astichi 1.1.3, YIDL 0.1.2, yidl-cache 0.1.0 and compat-sentinel 0.1.2.
See the [release compatibility contract](../RELEASE.md#yidl-compatibility-contract).

## Cache implementation

Caching is default-on and reuses compiled builders, not live model values. A
generation-free hit skips assembly and AST compilation; harvesting, validation,
fresh-namespace execution and runtime binding still occur. A final home hit
after failed local publication may already have generated code. Diagnostics
distinguish that case. YIDL remains a dependency even on a cache hit.

The adapter tries module-local private cache storage, then private home storage;
unsafe/unavailable locations fall through to generation. See
[user controls](../docs/Cache.md), the [integration record](LifecycleCodeCache.md)
and [startup measurements](LifecycleCodeCacheStartup.md).

## Develop and release

From this repository root:

```sh
PYTHONPATH=../astichi/src uv run --with pytest python -m pytest -q
```

Local development uses the configured sibling YIDL, Astichi and Cache sources;
published metadata uses named distribution dependencies. Read [RELEASE.md](../RELEASE.md)
before release work; Gearu is the release tool and publication runs in CI.

The [developer index](README.md) preserves current policies and historical
design/review evidence. The [end-user documentation spec](EndUserDocumentationSpec.md)
records the learning goals and research limits for the public guides.

See [documentation site maintenance](documentation/README.md) for local preview,
example/site checks and the GitHub Pages deployment workflow.
