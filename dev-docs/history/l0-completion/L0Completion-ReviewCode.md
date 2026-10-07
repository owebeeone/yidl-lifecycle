# L0 completion library checkpoint — Code-AXIS REVIEW

**Review object:** yidl-lifecycle `371dfa530a975c27f7a6c09a7648f7f00532ab29..30b7c83f3ef7a733a38a55b221a022aa7b7f8e84`, L0-1/L0-2 manager/generated-library checkpoint. Controlling document: `pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md`; design accepted, implementation acceptance pending as of 2026-10-08.
**Baseline:** Lifecycle baseline `371dfa530a975c27f7a6c09a7648f7f00532ab29`; candidate `30b7c83f3ef7a733a38a55b221a022aa7b7f8e84`. Pyrolyze `ac410240fc33459da31ffcc87863f915ed7e124e`; YIDL `a7cc1de7b630b55bd194940ecad83f3f1738cf8a`; Astichi `1c47f781d3804130fdd61cbee07a3b2e4529158a`. Documents and baseline source were read using `git show`; candidate source using `nl`, `rg`, and `git diff`. Inspected dependency files match their committed revisions.
**Date:** 2026-10-08
**Axis:** Code: architecture, interface contracts, call graphs, compatibility, and error provenance. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on it. Filed verbatim by the lane owner.

**Verdict: NO-GO** — one P2 finding blocks. I pre-commit to GO on a revision that resolves P2-1 as specified.

---

## 0. Evidence base

Unprefixed paths below are relative to the yidl-lifecycle repository.

- Read the local review-loop `SKILL.md`, parent and all four repository `AGENTS.md` files, and lifecycle `dev-docs/README.md`.
- Read the controlling plan, particularly Compatibility, Completion Observation, Completion Algorithm, Error Contract, and Implementation Checkpoints; also `dev-docs/TransactionScopeOwnership.md` and all of `dev-docs/L0CompletionVerification.md`.
- Inspected `src/yidl_lifecycle/transaction_yidl.py:1-917` and its baseline diff, including callback resolution, ownership checks, finalization, exception deduplication, and multi-key dispatch.
- Inspected core resources at `src/yidl_lifecycle/yidl/lifecycle_core.yidl:314-553` and contributions at `1059-1096`; managed writers/hooks at `lifecycle_managed.yidl:241-435`, `455-522`, `1116-1149`, and `1365-1462`; owned writers/preparation at `lifecycle_owned.yidl:141-287`; transient materialization at `lifecycle_transient.yidl:204-249`.
- Read `tests/test_transaction_yidl.py:1-1011`, the complete completion-failure fixture, its generated parent/child outputs, core-only output, changed golden hunks, regeneration implementation, golden harness, documentation commands, constructor-fixture changes, and lockfile change.
- Inspected Pyrolyze’s accepted SC3 caller/writer audit, `lifecycle_adapter.py:1-33`, `render_attempt.py:38-288`, fault tests at `test_runtime_context_state_lcm_render_attempt.py:482-636`, and historical `transaction_failures.py:1-152`.
- Ran the authorized manager command with native lowering, bytecode disabled, and pytest caching disabled: **85 passed**.
- Ran the authorized canonical fixture in memory through `render_case()` and `validate_case(outputs)`: **passed**. All six rendered files exactly matched checked-in artifacts. This does not independently rerun the complete decorator-to-YIDL consistency check, whose implementation and documented result were inspected.
- All four HEADs matched the specified tuple at start and end. The lifecycle tree remained clean; dependency tracked trees were clean. The two excluded Pyrolyze untracked documents were not read. No files were written, builds performed, or peer reports accessed.

## 1. Findings

### [P2-1] Diagnostic annotation can interrupt mandatory draining and erase recorded failures

**Location:** `src/yidl_lifecycle/transaction_yidl.py:283-294`, called from `354-355`; equivalent unguarded annotation at `369-372` and `735-737`. Generated wrappers repeat the root cause in `src/yidl_lifecycle/yidl/lifecycle_core.yidl:340-342` and `lifecycle_managed.yidl:519-521`.

**Violated invariant:** Preparation failure must discard every captured participant; independent eligible hooks must drain; the original exception must remain in terminal evidence. The controlling plan requires these behaviors at lines 225-229, 291-295, and 305-319.

**Code-traced reproduction:** Use the existing `CompletionContext` with A’s prepare error set to an instance of this legal exception subclass, enlist A then B, and call `commit_only()`:

```python
class NoteFailure(ValueError):
    def add_note(self, note):
        raise RuntimeError("note sink failed")
```

A’s preparation raises the original error. `_attempt()` catches it, but `_record()` invokes its overridable `add_note()` before retaining it. The annotation error escapes `_record()` and `_attempt()`, bypassing `commit()`’s preparation-failure rollback branch. The manager’s `finally` still finalizes the token. The resulting trace is `order:A; order:B; prepare:A`, with **no discard or after-rollback attempts**, and terminal `failures == ()`. The outward error is `"note sink failed"`, not the original failure. This custom counterexample was traced from source, not executed, because additional probes were outside the authorized commands.

The same error raised by the canonical parent after hook exits its generated exception handler before `failures.append(error)`, skipping the independent child hook. Thus the problem is not confined to legacy participants.

**Impact:** Exception reporting becomes an unprotected user-code call that defeats the central drain/report contract. Pending work can remain after ownership finalization, and retained completion evidence omits the triggering failure.

**Required correction:** Make diagnostic formatting and annotation non-throwing with respect to completion dispatch. Retain the original failure before attempting annotation. Apply the correction consistently to manager, scope, core, and managed annotation sites; regenerate artifacts from YIDL rather than patching generated output.

**Closure/regression test:** Add narrow manager cases using a throwing `add_note()` override during prepare and discard, asserting required traces, original exception retention, and accurate terminal flags. Exercise the same exception in inherited generated after-commit/after-rollback hooks, proving later independent hooks still run. Re-run the authorized manager/canonical checks and generated-source consistency checks.

## 2. Invariant analysis

- The ordinary failure attacks passed: preparation stops at its first failure; application continues independently; failed application receives pending discard; failed discard suppresses only its dependent after action. No current-value undo is claimed.
- Completion retention, readonly/frozen evidence, nested nonfinal completion, stale-scope fencing, required callback failures, optional callback absence, and legacy argument ordering are covered by the passing manager tests.
- Complete managed output preserves direct inherited/local hook calls with separate wrappers. Ordinary lone failures retain identity; grouped ordinary/system exceptions and repeated leaves retain provenance under the tested cases. P2-1 exposes an untested reporting escape.
- Transactional managed/owned setters and transient/materializing getters reach the common candidate-write check before mutation or factory/thaw. Existing-overlay reads remain permitted. The canonical fixture verifies prepared-target rejection, permitted before-hook staging, conversion/after rejection, and other-key isolation.
- No new marker syntax, enums, saved values, compiler changes, or cross-key atomicity were found.
- Pyrolyze’s owner still deliberately uses its older uncertainty/reuse policy. The documented historical probe and apply-error expectation transitions belong to consumer adoption, not this library correction. The Python/native owned-field exact-source mismatch remains documented as failing comparison, not a passing parity check.

## 3. Risks and next action

Full/version suites and prior-decorator Python snapshot reproduction were inspected as recorded evidence, not rerun. Retained-alias interception, live resource readiness, and consumer adoption remain deferred and are not certified here.

The next action is bounded remediation of P2-1, followed by same-axis closure of the original counterexamples at a newly pinned tuple.
