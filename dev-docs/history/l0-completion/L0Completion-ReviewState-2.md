# L0 completion library checkpoint — State-AXIS REVIEW (Remediation 1 Re-verdict)

**Review object:** `yidl-lifecycle` baseline..`4b86eec179942d96012aa4a1d92752a34cae87ef`, L0-1/L0-2 manager/generated-library checkpoint. Corrected parent: `30b7c83f3ef7a733a38a55b221a022aa7b7f8e84`. Controlling document: `pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md` at `ac410240fc33459da31ffcc87863f915ed7e124e`. Status: implementation candidate, Remediation 1 reviewed.
**Baseline:** `yidl-lifecycle` `371dfa530a975c27f7a6c09a7648f7f00532ab29`; dependencies: `pyrolyze` `ac410240fc33459da31ffcc87863f915ed7e124e`, `yidl` `a7cc1de7b630b55bd194940ecad83f3f1738cf8a`, `astichi` `1c47f781d3804130fdd61cbee07a3b2e4529158a`. Sources read through `git show`, parent-to-candidate diffs, and clean working-tree views.
**Date:** 2026-10-08
**Axis:** Completion authority, failure ordering, candidate-write boundaries, and fail-closed state recovery. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on it. Filed verbatim by the lane owner.

**Verdict: GO** — P2-1, P2-2, and P2-3 are CLOSED. No new findings from the bounded remediation review. The prior pre-commit conditions are satisfied.

---

## 0. Evidence base

Paths below are relative to the `yidl-lifecycle` repository unless another repository is named.

- Re-read applicable parent/repository `AGENTS.md` instructions and the local review-loop `SKILL.md`. Read the controlling plan, `dev-docs/L0Completion-RemPlan-1.md`, the original State report, updated `dev-docs/TransactionScopeOwnership.md`, and `dev-docs/L0CompletionVerification.md`, including Remediation 1 Verification at lines 141-184. No current-round peer report was inspected.
- Inspected the remediation diff and implementation at `src/yidl_lifecycle/transaction_yidl.py:126-146,254-408,410-533,596-706,755-779,821-826`. Checked declaration changes, original-identity capture, annotation ordering, validation fencing, finalization, and scope dispatch.
- Inspected declarative wrappers at `src/yidl_lifecycle/yidl/lifecycle_core.yidl:331-345` and `lifecycle_managed.yidl:515-524`, their generated counterparts, manager regressions at `tests/test_transaction_yidl.py:1016-1140`, complete-fixture extensions at `tests/data/gold_src/yidl_transactional_completion_failures.py:205-228,306-329`, and selected core-wrapper coverage at `yidl_transactional_lifecycle_core.py:146-158,233-260`.
- Ran the authorized manager command with bytecode/cache writes disabled and native backend selected: `env PYTHONDONTWRITEBYTECODE=1 ASTICHI_LOWER_ENGINE=native PYTHONPATH=src:../astichi/src:../yidl/src ../.venv/bin/python -m pytest -p no:cacheprovider -q --tb=short tests/test_transaction_yidl.py`. Result: **116 passed** on Python **3.12.12**.
- Rendered and validated both authorized canonical fixtures entirely in memory with native and Python backends. Both passed runtime assertions on both backends. All ten raw/prettier artifacts matched their checked-in snapshots exactly on each backend.
- Compared `render_lifecycle_base_source()` against the complete checked-in decorator entirely in memory: **exact YIDL-source match passed**. No regeneration CLI or output-writing operation was invoked.
- Independently executed the three original attacks against the parent manager loaded from `git show 30b7c83:...` and against the corrected manager. The parent reproduced all three defects; the corrected candidate passed the closure assertions. Also confirmed that prior generated parent/child sources fail the expanded hostile-parent identity assertion, while corrected canonical sources pass.
- Additional bounded probes passed: malformed-note `KeyboardInterrupt` followed by an independent cleanup failure; distinct equal public key values; empty commit/rollback phase evidence and original integer results.
- Start and end HEAD checks matched the complete settled tuple. Lifecycle, YIDL, and Astichi stayed clean; Pyrolyze retained only the two explicitly excluded untracked documents. Its controlling plan had no working-tree diff. No files, Git state, backend configuration files, or builds were changed.

## 2. Invariant analysis

### Original Finding Closures

| Finding | Exact counterexample and corrected result | Changed enforcement and regression evidence | Status |
| --- | --- | --- | --- |
| **P2-1: Annotation interrupts cleanup** | Re-ran A prepare raising an exception whose `add_note()` throws, with B enlisted. Parent stopped after `prepare:A`, raised the annotation error, and recorded zero failures. Corrected candidate raised the original exception unchanged, retained it, and attempted discard A/B followed by after-rollback A/B. Corrected inherited/local hooks also preserve the original hostile parent failure and drain child/later-participant hooks. | Retain-first guarded standard annotation at `transaction_yidl.py:293-309`, validation at `389-399`, scopes at `765-774`; declarative wrappers at `lifecycle_core.yidl:340-345` and `lifecycle_managed.yidl:519-524`. Nine annotation cases, multi-key scope regression, both canonical fixtures, and independent original-sequence probe **passed**. | **CLOSED** |
| **P2-2: Validation borrows the before-hook window** | Re-ran generated before-hook → public validation → validator assignment of 99 after staging 10. Parent published 99 and certified clean completion. Corrected candidate rejected validation before validator dispatch, published nothing, cleared pending work, and recorded successful discard/eligible after actions with preserved ownership and finalization. | `GroupTransactionManager.validate()` now fences completion before dispatch at `transaction_yidl.py:651-661`, specifically line 654. Canonical existing-overlay, untouched-field, thaw, and factory cases at `yidl_transactional_completion_failures.py:306-329` **passed**; permitted direct before-hook staging and independent-key validation remained passing. | **CLOSED** |
| **P2-3: Mutable metadata relabels terminal evidence** | Re-ran a generated after-commit hook changing transaction ID 1 to 2. Parent returned 2 and certified record ID 2. Corrected candidate retained record ID 1, reported authority loss, finalized the original manager ownership, and preserved published current value 10 without pretending undo. The following transaction legitimately received ID 2 and remained distinct from the original record. | Creation capture at `transaction_yidl.py:144-146`, session capture at `273-275`, identity checks at `317-323`, captured callback arguments at `362,369`, evidence at `523-525`, and results at `686,706`. Fourteen key/ID relabeling and replacement-token cases at `tests/test_transaction_yidl.py:1081-1140`, plus the exact generated original attack, **passed**. | **CLOSED** |

### Bounded Regression Attacks

Retain-first annotation preserves actual system exceptions and subsequent cleanup errors in deterministic order, even when notes are malformed. It does not substitute a diagnostic error or mark failed after actions complete. Complete and core-only generated paths select their wrappers and preserve direct hook references, lone exception identity, and `BaseExceptionGroup` behavior.

The validation correction is key-local. Standalone validation remains nonpublishing; independent-key validation remains available during another key's before hook. Existing self/later-participant staging, prepared-target rejection, conversion/after-write rejection, and materializing-getter protection remain passing.

Original identity checks do not require public callers to supply the identical key object: a probe using distinct equal keys passed begin, enlist, validate, sole-owner checking, and commit while retaining the creation key in evidence. Relabeling loses authority rather than inventing a replacement token. Replacement ownership remains untouched.

The 116-case manager run retains coverage of original failure traces, partial application mutations, missing callbacks, fixed ordering, nested/stale scopes, repeated exceptions, ownership loss, and empty phase-entry distinctions. No new marker/key syntax, enum state machine, field snapshots, current-value undo, compiler change, or cross-key atomicity was introduced. No additional architectural root cause was found in the bounded changes.

## 3. Risks and next action

This is a focused continuation, not a fresh full baseline review. Full native matrix results of 376 passed/46 skipped on Python 3.12/3.13/3.14 and the Python 3.13 focused count remain documentary evidence. This review independently executed Python 3.12.12 checks specified above.

The separate Python-owned-field snapshot discrepancy remains a failed exact-source comparison, not a passing result. Historical Pyrolyze transition cases remain obligations of later consumer adoption. This GO does not authorize activation, resource admission, retained-alias interception, thread safety, current-value undo, or process-restart durability.

The next action is lane-owner filing and verdict merge at this exact tuple. Acceptance still requires the independent other-axis verdict; private consumer adoption remains a separate checkpoint.
