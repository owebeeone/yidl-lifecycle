# ManagedContext API Proposal: Consistency Re-Review, Round 1

## Review Object
`dev-docs/ManagedContextApiProposal.md` and `docs/ManagedContextApiDraft.md` at `432a61b18021912783267f2ed677208d77802cd1`. The proposal remains the controlling DRAFT. Acceptance concerns design consistency only, not implementation readiness or operator approval.

## Per-Repo Baseline And Start/End Tuple Checks
| Repository | Required Revision | Start | End |
| --- | --- | --- | --- |
| `yidl-lifecycle` | `432a61b18021912783267f2ed677208d77802cd1` | Exact match | Exact match |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Exact match | Exact match |

Both checks used the prescribed `git rev-parse` commands. The tuple remained unchanged. A scoped revision diff confirmed no changes to runtime source, tests, goldens, repository instructions, or the lifecycle controlling plans.

## Date
2026-10-03

## Axis
Consistency. Independent, adversarial, read-only review. No current-round peer prompts or reports were consulted.

## Verdict
**GO.** Open findings: P0: 0; P1: 0; P2: 0; P3: 0.

## Prior-Finding Closure Table
| ID | Disposition claimed | Verified on corrected tree | Status |
| --- | --- | --- | --- |
| Consistency P2-1 | Restrict decorator equivalence to the LCM alias; distinguish the legacy decorator and markers | Proposal lines 12-16 and guide lines 6-9 now identify the exact boundary. Retraced the adapter import at `../pyrolyze/src/pyrolyze/runtime/context_state_lcm/lifecycle_adapter.py:8` and legacy definition/rejection paths at `../pyrolyze/src/pyrolyze/lifecycle.py:3939` and `:3797-3816`. | Closed |
| Consistency P3-1 | Remove A2’s characterization of rewritable static as the selected proposal | Proposal line 152 now says “replacement policy unresolved under A5”. This agrees with lines 59, 299-327, 377-383 and guide lines 172-177. | Closed |

Closure was established through inspection commands and source/text retracing. Neither original counterexample was executed, and neither closure requires a runtime change.

## Changed-Range Analysis
The object diff implements the recorded dispositions: qualified decorator identity, outermost completion and `commit_only` wording, healthy-state getter qualifications, stale-state reuse warnings, acceptance-before-publication limits, complete custom-key setup, and explicit constructor-option defaults.

The added evidence link distinguishes committed-generated-golden characterization from live generation. These changes remain within `dev-docs/ManagedContextApiProposal-RemPlan-1.md`’s dispositions; no unlisted API, architectural, transaction-boundary, or static-policy change was established.

**NEW ARCHITECTURAL ROOT CAUSE: none identified.**

## Evidence Base
- Read both revised objects, the remediation plan, and `dev-docs/ManagedContextApiProposal-Checks.md` using `git show` at the revised revision.
- Used the original Consistency review’s controlling-document inspection, verified those documents unchanged, and re-read affected clauses in `AGENTS.md`, the Phase F-1 plan, close-the-gap plan, field matrix, parity plan, and pinned Pyrolyze integration plan.
- Retraced revised claims through `transaction_yidl.py`, core/managed/owned resources, binding acceptance, marker defaults, and the characterization recipe’s fixture and generated-output sources.
- Inspected the recipe; did not execute it. Its recorded successful observations are supplied evidence, not independently reproduced results in this lane.
- No writes, builds, tests, generation, network calls, or Git mutations were performed.

## Findings
None open. Both original Consistency findings are corrected, and the changed ranges yielded no additional reproducible consistency defect.

## Invariant Analysis
- **Completion/defaults:** The revised ordinary-completion guarantee matches `transaction_yidl.py:211-250`: nested completion reduces depth; outermost `commit` validates; `commit_only` proceeds without invoking validators. Explicit-key examples and omitted-key semantics remain consistent with manager normalization.
- **Failure/recovery:** The stale-overlay warning matches early-return getters and token checks in `lifecycle_managed.yidl:307-340` and `lifecycle_core.yidl:420-443`. It no longer equates manager reset or a fresh begin with participant recovery.
- **Owned effects:** Proposal lines 199-213 agree with `lifecycle_owned.yidl:271-287`: acceptance precedes staging/publication, and map acceptance may stop after a prefix. Reference rollback is not presented as undoing acceptance.
- **Constructor aliases:** A4’s defaults, resolved inheritance rules, provider identity, legacy-metadata fallback, and proposed-only status remain unchanged. The guide’s `init=False` clarification agrees with that contract.
- **Controlling graph:** A5 remains unresolved despite historical matrix wording. A6 preserves construction-before-attachment and existing completion cohorts; L0/D4 is not self-closed. No completed superseded-clause list or broader migration is claimed.
- **Evidence:** The recipe’s four scenarios are consistent with the inspected fixtures, generated goldens, and runtime ordering. The documented live-pipeline failure remains a verification limit, not a passing gate or repaired defect.

## Risks And Next Action
The live-decorator walkthrough remains unverified, as recorded in `dev-docs/ManagedContextApiProposal-Checks.md:157-184`. Diagnose that limitation separately before work relying on live decoration.

This GO accepts the corrected documentation proposal only. It does not approve `init_name`, select static behavior, certify runtime recovery, close L0/D4, or authorize further Pyrolyze integration.
