# Constructor annotation binding

## Authorized boundary

Deliverables: a TDD fix for runtime constructor annotations, regenerated owned
artifacts, focused regressions, full backend checks, and this evidence. Changes
are confined to Lifecycle YIDL, necessary harvester/factory/cache-schema wiring,
owned artifacts, tests, and developer documentation. Generic YIDL, Astichi,
yidl-cache, Dataclass, Undoable, Pyrolyze, GEARU, GWZ metadata, and the paper are
reference-only. The operational isolation marker was present before editing;
original-candidate remote results remain separate. No Git mutations are authorized.

## Fix and requirement provenance

The constructor templates literalized annotation objects with
`astichi_bind_external(annotation)`, which rejects live types. Shared required,
defaulted, and factory parameter resources now omit those bindings. The generated
factory captures a separate constructor-annotation mapping and assigns it to
`__init__.__annotations__` after defining the constructor. The harvester builds
that mapping from effective field facts, including inheritance/overrides and
excluding non-init fields, classvars, and local stores. Local class annotations,
default/factory identity, and unresolved annotation strings retain their meaning.

Optional verification on the already-supported Python 3.14 exposed deferred
annotations missing from `cls.__dict__`. The coordinator explicitly included this
narrow harvesting correction. Runtime inspection on 3.12/3.14 showed that
`inspect.get_annotations(cls, eval_str=False)` rejects explicit `MappingProxyType`
annotations accepted previously. `dict(getattr(cls, "__annotations__", {}))` is
the smaller equivalent that supports deferred annotations, retains local-only
class behavior and explicit mappings, and leaves strings unevaluated.

The cache's class-key allowlist accepts the additional parameter name. Its
exact-string-only annotation admission, live-annotation bypass, and source
invalidation policy remain unchanged; no generator revision or dependency change
was needed. Annotations are runtime builder data, not compiled constants.

## TDD evidence

Tests were added before the corresponding production edits. Compiler-path checks
use `YIDL_LIFECYCLE_CACHE=off` and `PYTHONDONTWRITEBYTECODE=1`. The regression module
has no future-annotations import; its postponed-string case compiles explicitly
with `dont_inherit=True`.

| Stage | Interpreter/engine | Result |
| --- | --- | --- |
| Constructor RED | 3.12.12 / python | 23 failed: 21 rejected live types, 2 double-quoted string annotations |
| Initial constructor GREEN | 3.12.12 / python | 23 passed |
| Expanded constructor/harvester/regeneration checks | 3.12.12 / native-rust | 57 passed |
| Deferred-harvesting RED before retrieval edit | 3.14.3 / python | 24 failed, 33 passed |
| Targeted local/mapping harvesting RED | 3.14.3 / python | 1 failed, 1 passed, 26 deselected |
| Both fixes GREEN, focused checks | 3.14.3 / python | 59 passed |
| Both fixes GREEN, runtime/harvester subset | 3.13.12 / python | 57 passed |

The first RED command was:

```sh
ASTICHI_LOWER_ENGINE=python YIDL_LIFECYCLE_CACHE=off PYTHONDONTWRITEBYTECODE=1 \
  ../.venv/bin/python -m pytest tests/test_lifecycle_annotations.py -q
```

Coverage includes live user-defined types through required/default/factory
constructors for plain, initvar, const, managed, transient, owned, and binding
fields; mutable lazy with `int`; inherited/overridden types; non-init exclusion;
explicit/postponed unresolved strings; local-only harvesting; and explicit
annotation mappings. The fixture uses a stored-field anchor for initvars and a
valid user-defined `BindingBase` value for owned/binding fields. These prerequisite
corrections preserved the original annotation assertions.

A separate cache check confirms actual live-annotation `CacheBypass` with no
persisted `.ycode`, round-trips one builder code object with `marshal`, and binds
two same-named but distinct live types through that same reloaded builder.

## Regeneration and full verification

Use explicit `ASTICHI_LOWER_ENGINE=native-rust` for canonical regeneration:
`python -m yidl_lifecycle.regenerate_lifecycle_base --write`, affected cases via
`yidl.testing.versioned_test_harness.run_golden_case`, and
`python tests/data/perf/generate_lifecycle_constructor_perf_fixture.py`.
The core golden now supplies actual `int` facts; the independent phase-A fixture
is unchanged. All **24** changed canonical generated-output ASTs match their
originals after removing only the intended captured parameter, constructor
annotation literals, and annotation assignment. Source-shape assertions remain.

Full runs after both fixes use the cache-disabled environment above and
`python -m pytest tests -q`. Selection snapshots report the requested engine as
selected with `fallback_scope=None`.

| Interpreter | Explicit engine | Full result |
| --- | --- | --- |
| CPython 3.12.12 | native-rust | 462 passed, 46 skipped |
| CPython 3.12.12 | python | 461 passed, 46 skipped, 1 known owned-field source mismatch |
| CPython 3.14.3 | python | 461 passed, 46 skipped, 1 known owned-field source mismatch |

The 3.12 extension `../astichi/native_engine/_astichi_native_engine.cpython-312-darwin.so`
passes `native_self_test()` and matches the operationally rebuilt release dylib:
SHA-256 `8266d234e9de1767b04c7a8291727b70164d3e6376f2562651252fa363f895c5`.
The additional 3.14 run explicitly uses Python, avoiding the older 3.14 extension.
Generated-base equality, changed-source syntax, and `git diff --check` pass.
The new regression module passes Black's Python-3.12 check. No dependencies, GWZ
metadata, or history/archive files were edited; no commits, tags, pushes, branches,
or worktrees were created.

## Separate findings

- **Confirmed existing defect; does not block this fix:** an initvar-only class
  with `seed: 'int' = initvar(default=2)` fails with unresolved `state_slots`, even
  with strings and cache disabled. Add an explicit empty slot-hole fallback or
  equivalent no-storage generation support in a separate change.
- **Confirmed existing source-rendering difference; does not block annotation
  behavior:** the owned-field golden differs between Python and native-rust
  (`value` versus `value__astichi_scoped_1`). Retain the native canonical output
  and investigate source parity separately; no assertion was weakened.
- **Verification environment limitation; does not block other full runs:** the
  existing 3.13 environment lacks `lark`, preventing optional parser/regeneration
  test collection. Its generated-builder runtime path passes. Provision the
  declared development dependencies separately if full 3.13 coverage is needed;
  no installation was necessary or performed for this fix.
