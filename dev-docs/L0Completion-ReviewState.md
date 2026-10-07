# L0 completion library checkpoint — State-AXIS REVIEW

**Review object:** `yidl-lifecycle` baseline..`30b7c83f3ef7a733a38a55b221a022aa7b7f8e84`, L0-1/L0-2 manager/generated-library checkpoint. Controlling document: `pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md` at `ac410240fc33459da31ffcc87863f915ed7e124e`. Status: implementation candidate, reviewed 2026-10-08.
**Baseline:** `yidl-lifecycle` `371dfa530a975c27f7a6c09a7648f7f00532ab29`; pinned dependencies: `pyrolyze` `ac410240fc33459da31ffcc87863f915ed7e124e`, `yidl` `a7cc1de7b630b55bd194940ecad83f3f1738cf8a`, `astichi` `1c47f781d3804130fdd61cbee07a3b2e4529158a`. Sources were read through `git show`, baseline-to-candidate diffs, and clean working-tree views.
**Date:** 2026-10-08
**Axis:** State machines, completion authority, failure ordering, candidate-write boundaries, and fail-closed recovery evidence. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on it. Filed verbatim by the lane owner.

**Verdict: NO-GO** — three P2 findings block. I pre-commit to GO on a revision that resolves P2-1, P2-2, and P2-3 as specified.

---

## 0. Evidence base

- Read the parent and four relevant repository `AGENTS.md` files, the local review-loop `SKILL.md`, and the lifecycle documentation index. Read the controlling plan, particularly Completion Observation, Candidate-Write Boundary, Required Failure Traces, Error Contract, and L0-1/L0-2.
- Read `yidl-lifecycle/dev-docs/TransactionScopeOwnership.md:1-95` and `dev-docs/L0CompletionVerification.md:1-134`. Reviewed the latter's matrix, prior-decorator reproduction, and historical Pyrolyze transition disposition; those are documentary evidence, not independently repeated executions.
- Inspected `yidl-lifecycle/src/yidl_lifecycle/transaction_yidl.py:1-917`, its complete baseline-to-candidate diff, and the baseline implementation. Traced session capture, callback attempts, phase flags, ownership checks, finalization, scopes, and multi-key dispatch.
- Inspected core resources at `src/yidl_lifecycle/yidl/lifecycle_core.yidl:331-343,436-549,1060-1097`, managed writers/helpers/contributions at `lifecycle_managed.yidl:243-438,466-575,1125-1148`, and owned/transient writer and cleanup resources. Compared the corresponding generated-decorator changes, core golden, hook golden, and constructor-performance artifact changes.
- Read `tests/test_transaction_yidl.py`, the canonical completion-failure fixture, and generated inherited/local dispatch at `tests/data/goldens/materialized/yidl_transactional_completion_failures/generated_output_prettier.py:138-286,295-419`. Read the regeneration consistency test and its implementation without executing regeneration.
- Ran the authorized manager command from `yidl-lifecycle`: `env PYTHONDONTWRITEBYTECODE=1 ASTICHI_LOWER_ENGINE=native PYTHONPATH=src:../astichi/src:../yidl/src ../.venv/bin/python -m pytest -p no:cacheprovider -q --tb=short tests/test_transaction_yidl.py`. Result: **85 passed**.
- Ran the authorized in-memory canonical fixture through `runpy.run_path`, `render_case()`, and `validate_case(outputs)`, with its source directory on `PYTHONPATH`. Runtime assertions passed; all six rendered raw/prettier decorator, parent, and child artifacts exactly matched their checked-in snapshots. This does not independently establish full decorator-to-YIDL regeneration equality.
- Start and end `git rev-parse HEAD` checks matched every SHA above. Lifecycle, YIDL, and Astichi remained clean; Pyrolyze contained only the two explicitly excluded untracked documents. Its controlling plan had no working-tree diff. No files were written, builds performed, or peer reports inspected. Finding reproductions below are deterministic source-derived sequences, not additional executed probes.

## 1. Findings

### [P2-1] Exception annotation can abort mandatory cleanup and erase the original failure

**Location:** `yidl-lifecycle/src/yidl_lifecycle/transaction_yidl.py:283-294,354-355,368-372`; generated-wrapper sources `src/yidl_lifecycle/yidl/lifecycle_managed.yidl:519-521` and `lifecycle_core.yidl:340-342`. The emitted managed instance is visible at `tests/data/goldens/materialized/yidl_transactional_completion_failures/generated_output_prettier.py:308-310`.

**Violated invariant:** Original exceptions must survive, and independent discard/eligible after actions must drain despite callback failures. Annotation is currently an unprotected operation performed before recording the exception.

**Reproduction/state sequence:** Define a valid exception subclass whose `add_note(self, note)` raises `RuntimeError("notes failed")`. Enlist A and B, then have A's prepare callback raise an instance E. `_attempt` catches E, but `_record` invokes E's overridden method and throws before retaining E. Control exits `session.commit()` before either discard; `finally` finalizes the manager and installs evidence with an empty `failures` tuple. Separately, a generated parent's after hook raising E causes its wrapper's annotation to throw before the local child hook is attempted. The manager records the annotation error instead of E.

**Impact and required correction:** Error reporting becomes a new interruption point, leaving pending work uncleared and defeating inherited/local draining and original-error identity. Make annotation best-effort and non-interrupting throughout manager and generated paths; retain the original exception before annotation. Correct the YIDL resources and regenerate their artifacts, not just emitted Python.

**Closure test:** Add a narrow manager failure test using this subclass during preparation and discard; assert independent cleanup attempts, original E retention, and accurate completion flags. Extend canonical inherited/local hook failure coverage so an annotation-hostile parent exception cannot suppress the child or later participant.

### [P2-2] Reentrant validation inherits the before-hook candidate-write window

**Location:** `yidl-lifecycle/src/yidl_lifecycle/transaction_yidl.py:271-280,622-630`; the generated setter reaches this permission check through `src/yidl_lifecycle/yidl/lifecycle_core.yidl:436-451`.

**Violated invariant:** Validation cannot create candidates during final completion. An open before-hook window must not grant validation callbacks candidate-write authority.

**Reproduction/state sequence:** Use a generated participant with a managed `count`, a validator that executes `self.count = 99` and returns `True`, and a before hook that calls `manager.validate(DEFAULT_TRANSACTION)`. Begin, stage `count = 10`, and call `commit_only(DEFAULT_TRANSACTION)`. The deliberate initial validation bypass reaches the before hook. Public `validate()` neither rejects completion-time entry nor suspends the existing window. Its validator's setter sees the captured, unprepared participant and passes `_require_candidate_write`. Preparation then freezes 99, application publishes 99, and completion reports publication, after actions, ownership, and finalization successful with no failures.

**Impact and required correction:** The documented no-write validation boundary is bypassed through public manager APIs, without retained aliases or private-state tampering. Reentrant validation must not inherit candidate permission: reject same-key validation during completion or suspend that permission throughout its dispatch. Preserve ordinary standalone validation and independent other-key behavior.

**Closure test:** Extend the canonical generated fixture with before-hook-to-validation reentry against an existing overlay, an untouched field, and a materializing getter. Assert rejection before candidate mutation/factory/thaw, no application, drained eligible cleanup, and coherent terminal evidence. Keep the existing permitted before-hook self/later-participant writes passing.

### [P2-3] Completion rereads mutable token metadata instead of retaining the original key and ID

**Location:** `yidl-lifecycle/src/yidl_lifecycle/transaction_yidl.py:265-269,296-314,500-503,655,675`. `LifecycleTransaction.tx_id` and `tx_key` are writable fields at lines 126-129.

**Violated invariant:** The retained record and completion result must describe the original key/token. Ownership certification must not silently accept changed token identity metadata.

**Reproduction/state sequence:** Begin the default transaction with ID 1, stage one generated participant, and have its after-commit hook execute `transaction.tx_id = 2`. Application has already succeeded and cleared its working token. `_check_ownership` still passes because it checks object identity, nesting, and participant sequences, but not key/ID metadata. Finalization emits `completion.tx_id == 2` with `ownership_preserved=True`; `commit_only()` returns 2. The next ordinary begin also receives ID 2 from the unchanged manager counter. Reassigning `tx_key` similarly mislabels terminal evidence.

**Impact and required correction:** The original transaction receives a certificate naming a different token, and the integer return regresses from the baseline, which captured `tx_id` before callbacks. Capture original key/ID independently and use them for callback arguments, diagnostics, terminal evidence, and results. Prevent metadata reassignment or detect it as authority loss; do not issue clean ownership evidence for a relabeled token.

**Closure test:** Parameterize key/ID reassignment during preparation and after completion actions. Require either rejection before mutation or fail-closed authority evidence, with the record still identifying the original token. Verify subsequent transactions cannot be confused with that record and replacement transactions remain untouched.

## 2. Invariant analysis

The principal failure traces held under the executed tests: first prepare failure stops dependent preparation but drains discard; throwing application can mutate current state and still permits independent later application; failed discard makes its dependent after action ineligible. Empty entered phases are distinguished from unentered phases, including eligible-empty after dispatch following failed discard.

Fixed descending order, stable equal-rank ordering, nested nonfinal completion, stale ordinary/exceptional scopes, body-error aggregation, missing required versus optional callbacks, legacy fallback, same-key membership/reentry guards, and replacement-token fencing passed. Ownership loss prevents certification and does not discard a replacement. Repeated original exceptions and nested hook groups retain leaf identity in the covered cases.

The canonical fixture confirmed normal inherited/local hook draining, direct method references, clean unpublished discard followed by reuse, permitted before-hook staging, and rejected prepared-target/conversion/after/materializing writes. Core and managed declarative changes correspond structurally to their generated counterparts. P2-1 and P2-2 expose exceptions to those otherwise successful boundaries.

No new marker/key syntax, enum state machine, saved-value undo, or cross-key atomicity was found in the changed runtime surface. The library is in-memory and specifies no filesystem durability or process-restart protocol; no such guarantee was inferred from its completion record. Thread safety and retained-payload alias interception remain explicitly deferred.

## 3. Risks and next action

Full/version/backend verification was not repeated beyond the authorized commands. The Python-owned-field exact-source mismatch remains a documented failed comparison, not a passing check. The two historical Pyrolyze transition differences belong to later consumer adoption; neither was treated as unrelated debt or silently closed here.

The next action is one bounded remediation of P2-1 through P2-3, with their closure tests, followed by same-axis verification at a newly settled tuple. This checkpoint must not be accepted or used as a completion-authority prerequisite before those findings close.
