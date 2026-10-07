# L0 Completion Verification

Updated: 2026-10-08. Status: implementation candidate; independent Code/State
acceptance review and private Pyrolyze consumer adoption remain pending.

## Scope

This checkpoint implements L0-1 and L0-2 of
[the accepted contract](../../pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md).
It does not activate live rendering, admit resource-bearing routes, migrate
callback holders, change marker semantics, or provide atomic multi-key commit.

- Original transaction objects retain immutable terminal completion evidence.
- Completion captures participants/order once, drains independent application
  and eligible cleanup, and preserves original failures and partial outcomes.
- Generated before hooks have a bounded candidate-write window. A target's
  permission closes before field conversion, including existing overlays.
- Generated inherited/local after hooks run independently. A sole failure is
  raised unchanged; multiple failures preserve nested groups and original leaves.
- The complete decorator, canonical outputs, and constructor performance
  fixtures were regenerated from their owning source, not manually patched.

## Verification

| Check | Result |
| --- | --- |
| Full library, Python 3.12, native backend | 345 passed, 46 skipped |
| Full library, Python 3.13, native backend | 345 passed, 46 skipped |
| Full library, Python 3.14, native backend | 345 passed, 46 skipped |
| Manager mechanics | 85 passed |
| Focused manager/decorator/parity, Python 3.12 | 193 passed, 46 skipped |
| Focused manager/decorator/parity/goldens, Python 3.14 native | 204 passed, 46 skipped |
| Focused manager/decorator/parity/goldens, Python 3.13 Python backend | 203 passed, 46 skipped; one pre-existing owned-field source snapshot mismatch |
| Generated decorator consistency | Matches its YIDL source |
| Completion-failure fixture, native | Rendered source and runtime assertions pass |
| Completion-failure golden, Python 3.12 Python backend | Exact source comparison and runtime assertions pass |
| Existing Pyrolyze seven-file baseline | 125 passed; two expected library-transition differences, disposition belongs to consumer adoption |

The three full native runs cover the configured supported-Python matrix.
The Python-backend cross-version row is a focused check, not a full-suite
claim. Skips remain existing deferred parity coverage, not new L0 exclusions.

From this repository root, run each full native suite with:

```sh
env PYTHONDONTWRITEBYTECODE=1 ASTICHI_LOWER_ENGINE=native \
  PYTHONPATH=src:../astichi/src:../yidl/src \
  uv run --frozen --python 3.13 --extra dev python -m pytest \
  -p no:cacheprovider -q --tb=short
```

Select `3.12` or `3.14` for the other matrix entries. The native extension
must be built for the selected interpreter; rebuilding it belongs to Astichi.

## Python Owned-Field Snapshot Disposition

On Python 3.13 with `ASTICHI_LOWER_ENGINE=python`, the owned-field fixture
produces hygienic temporary names such as `value__astichi_scoped_1`, whereas
the checked-in native output uses `value`. Both raw/prettier outputs pass
the fixture's runtime assertions; exact source comparison fails.

The same discrepancy was reproduced with the prior committed lifecycle
decorator and fixture at `371dfa530a975c27f7a6c09a7648f7f00532ab29`, against
the current compiler dependencies, without reverting or modifying checkout
files. The candidate produces the same discrepancy. This is not an L0
regression and is not classified as a passing source-snapshot check. No
snapshot was normalized, assertion disabled, or compiler changed to hide it.

Reproduce the prior-decorator observation from this repository root:

```sh
env PYTHONDONTWRITEBYTECODE=1 ASTICHI_LOWER_ENGINE=python \
  PYTHONPATH=src:../astichi/src:../yidl/src:tests/data/gold_src \
  uv run --python 3.13 --extra dev python - <<'PY'
import difflib
import importlib
import subprocess
from types import ModuleType

revision = "371dfa530a975c27f7a6c09a7648f7f00532ab29"
fixture_path = "tests/data/gold_src/yidl_transactional_phase_h_owned.py"
decorator_path = "src/yidl_lifecycle/_generated_lifecycle_base.py"
golden_dir = "tests/data/goldens/materialized/yidl_transactional_phase_h_owned/"

def source(path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], text=True)

frontend = importlib.import_module("yidl_lifecycle.lifecycle")
generated = ModuleType("_baseline_lifecycle_decorator")
decorator = source(decorator_path)
exec(compile(decorator, decorator_path, "exec"), generated.__dict__)
frontend._generated_lifecycle_base_module = lambda: generated
fixture = ModuleType("_baseline_owned_fixture")
exec(compile(source(fixture_path), fixture_path, "exec"), fixture.__dict__)
outputs = dict(fixture.render_case())
outputs["decorator.py"] = decorator
outputs["decorator_prettier.py"] = fixture._prettier_source(decorator)
fixture.validate_case(outputs)
print("Prior-decorator runtime assertions pass")
for name in ("generated_output.py", "generated_output_prettier.py"):
    expected = source(golden_dir + name)
    actual = outputs[name]
    print(name, "source match:", expected == actual)
    difference = difflib.unified_diff(expected.splitlines(), actual.splitlines())
    print("\n".join(list(difference)[:18]))
PY
```

## Dependency Tuple

The candidate was verified against:

- Astichi: `1c47f781d3804130fdd61cbee07a3b2e4529158a` (released 1.1.3).
- YIDL: `a7cc1de7b630b55bd194940ecad83f3f1738cf8a`.
- Pyrolyze: `ac410240fc33459da31ffcc87863f915ed7e124e`.
- Lifecycle baseline: `371dfa530a975c27f7a6c09a7648f7f00532ab29`; candidate
  revision will be pinned by the implementation-review reports.

No parent submodule pointers, compiler code, or Pyrolyze runtime were changed.
The editable Astichi entry in `uv.lock` now records the tested release, 1.1.3;
other lockfile metadata and the existing dependency surface are unchanged.

## Acceptance Gate

Fresh peer-blind Code and State reviews must judge the same committed candidate
against the accepted contract, including the original failure traces and the
generated inherited-hook/write-window behavior. No implementation acceptance
is claimed until both report GO at the same tuple.

The later private-consumer checkpoint owns the two Pyrolyze transition differences:
`test_unclassified_commit_failure_is_not_rolled_back_or_retried[apply_error]`
and `test_lifecycle_failure_completion_characterization_baseline`. Preserve
their historical observation/revision and introduce separately named current
outcomes; do not silently rewrite history or treat these as unrelated debt.
