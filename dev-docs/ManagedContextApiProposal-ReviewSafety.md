# ManagedContext API Proposal: Safety Review

## Review Object
Design review of `dev-docs/ManagedContextApiProposal.md` and `docs/ManagedContextApiDraft.md` at `128a3f24a1fdce425587bb790f6d424c6307a140`. The proposal is controlling. Runtime implementation and expressly deferred integration changes are not acceptance targets.

## Per-Repo Baseline And Start/End Tuple Checks
| Repository | Required revision | Start | End |
| --- | --- | --- | --- |
| `yidl-lifecycle` | `128a3f24a1fdce425587bb790f6d424c6307a140` | Matches | Matches |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Matches | Matches |

The proposal’s historical source baseline is `cdf08544deea846bca4fa7e0c468ebee8d41e138`; comparison with the reviewed revision confirms only the two document additions. Uncommitted review outputs were excluded.

## Date
2026-10-03

## Axis
Safety. Independent, peer-blind, read-only review.

## Verdict
**NO-GO. P0: 0; P1: 0; P2: 3; P3: 0.**

These are contract-wording defects, not demands to implement deferred runtime hardening.

## Evidence Base
- Both review documents were read using `git show` at the pinned revision.
- Controlling references inspected: repository `AGENTS.md`, Phase F-1, Close-The-Gap, Field-Kind Matrix, Lifecycle Parity, and the pinned Pyrolyze integration plan.
- Behavior cross-checked against `transaction_yidl.py`, lifecycle markers/harvester, managed/owned generation resources, materialized hook/owned goldens, and existing transaction failure fixtures.
- The pinned Pyrolyze lifecycle adapter confirms the decorator alias. Historical matrix/parity contradictions were not treated as implemented guarantees.
- Counterexamples below are source-derived, not executed. No tests, builds, generation, edits, network calls, or git mutations were performed. Current-round peer prompts/reports were not read.

## Findings

### P2-1: Completion Wording Hides Validator Bypass
- **Location:** `dev-docs/ManagedContextApiProposal.md:69` and `:84`.
- **Invariant:** An operation capable of irreversible publication must disclose whether validation is performed and its caller-owned preconditions.
- **Concrete counterexample:** Declare a managed integer with a validator rejecting negative values. Begin its explicit key, assign `-1`, then call the documented `obj.commit_only(key)` convenience. `GroupTransactionManager.commit_only` prepares and applies without invoking validation (`src/yidl_lifecycle/transaction_yidl.py:211`); generated preparation runs before-hooks and field preparation, not validators. The rejected value becomes current without an exception.
- **Impact:** “Normal completion validates” incorrectly includes an exposed completion path unless explicitly qualified. An author can bypass a business invariant while believing the documented completion contract still applies.
- **Correction:** Limit that guarantee to outermost `commit` and successful scope exit. Explain that `commit_only` bypasses validators, performs publication, and is appropriate only when its owner deliberately assumes validation responsibility. Explain that a prior `validate` does not certify subsequent edits; recommend `commit` for ordinary completion.
- **Closure check:** Re-read both drafts for consistent operation-specific wording. Add a narrow characterization showing the rejecting validator prevents publication through `commit` but is not invoked by `commit_only`; do not change runtime semantics merely to close this documentation finding.

### P2-2: Inactive Working-View Guarantee Fails After Interrupted Cleanup
- **Location:** `dev-docs/ManagedContextApiProposal.md:124`; `docs/ManagedContextApiDraft.md:92` and `:99`.
- **Invariant:** Degraded-state guidance must not equate inactive manager bookkeeping with cleared participant state or safe reuse.
- **Concrete counterexample:** Begin key K. Enlist a rollback-throwing participant first, as supported by the existing `FakeContext` fixture, then thaw and edit a `Numbers` participant. Rollback stops at the first participant; the manager resets, but Numbers retains its working list/token. Its working getter returns that list before checking transaction activity (`tests/data/goldens/materialized/yidl_transactional_phase_f_hooks/generated_output.py:525`). In a fresh transaction, the same getter again returns the stale list without enlistment; appending and completing does not publish it. Generated assignment instead rejects the old token (`:72`).
- **Impact:** Despite the acknowledged cleanup limitation, the draft’s unconditional “outside a transaction” guarantee is false. Freshly reacquired working references can expose failed edits and allow silently uncommitted mutations; discarding previously escaped references is insufficient.
- **Correction:** Qualify the facade table and aggregate guidance as healthy-state behavior. Explicitly warn that interrupted cleanup can leave visible stale overlays and unusable tokens, and that beginning another transaction does not recover them. Require verified cleanup or supported recovery before reuse; otherwise stop using the affected state cohort.
- **Closure check:** Add a focused failure characterization with the throwing participant preceding a generated aggregate. Confirm inactive stale reads, failed reenlistment on getter reuse, and stale-token assignment rejection. Documentation must describe these observations without claiming L0/D4 is implemented.

### P2-3: Owned Acceptance Can Survive Failed Preparation
- **Location:** `dev-docs/ManagedContextApiProposal.md:69`, `:102`, and `:174`.
- **Invariant:** Failure boundaries must distinguish transactional reference publication from automatic, non-transactional resource acceptance, including effects before publication.
- **Concrete counterexample:** On one key, order an owner participant before a participant whose `freeze` raises. Stage a caller-held `BindingBase` in the owner’s `owned` field. Owner preparation calls `accepted()` before staging (`src/yidl_lifecycle/yidl/lifecycle_owned.yidl:271`); later preparation fails. Rollback clears the pending reference but does not reverse acceptance. The owner’s current reference remains unchanged while the candidate’s `is_accepted` remains true (`src/yidl_lifecycle/bindings.py:31`). Owned maps can likewise accept a prefix before a later item fails.
- **Impact:** The text explains arbitrary resource-internal mutation but omits this generated effect. Authors can wrongly use successful field publication as the acceptance boundary, or treat a preparation failure as proof that candidates were never accepted.
- **Correction:** Document the pinned `owned` behavior explicitly: acceptance occurs during preparation, can be partial, and is not undone by reference rollback. Restrict pre-publication guarantees to current-slot replacement, not resource effects. Preserve deferred lifetime and acceptance-timing decisions.
- **Closure check:** Add a narrow preparation-failure characterization asserting unchanged current references alongside persistent candidate acceptance, including a partial owned-map case. Ensure both documents distinguish this from after-publication failure.

## Invariant Analysis
Completion ownership, omitted-key expansion, joined nesting, independent multi-key completion, and serialized-access requirements are explicitly bounded. The documents do not promise snapshots, isolation, graph-wide atomicity, publication undo, or implemented failure draining.

Shallow aggregate separation, mutable const referents, non-transactional storage, and escaped-reference limitations are acknowledged. The remaining safety defects are the operation-specific validation boundary, contaminated-state reuse boundary, and automatic owned-acceptance boundary.

No separate safety defect was established in constructor-only alias identity, proposed-only availability, static decision deferral, or initialization-versus-attachment scope.

## Risks And Next Action
Resolve P2-1 through P2-3 in the text without changing runtime behavior or expanding integration authority. The proposed closure checks characterize existing failures; none were run in this read-only review.

**I pre-commit to GO on a revision that resolves {P2-1, P2-2, P2-3} as specified.** Acceptance would remain design-review acceptance, not implementation approval or closure of L0/D4.
