# ManagedContext API Proposal: Safety Re-Review, Round 1

## Review Object
`dev-docs/ManagedContextApiProposal.md` and `docs/ManagedContextApiDraft.md` at `432a61b18021912783267f2ed677208d77802cd1`. The proposal is controlling.

This re-review checks correction of the original Safety findings and attacks the changed text for additional defects. It is design review, not implementation acceptance or authorization to resume integration.

## Per-Repo Baseline And Start/End Tuple Checks
| Repository | Required revision | Start | End |
| --- | --- | --- | --- |
| `yidl-lifecycle` | `432a61b18021912783267f2ed677208d77802cd1` | Matches | Matches |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Matches | Matches |

Original reviewed revision: `128a3f24a1fdce425587bb790f6d424c6307a140`. Source and test comparison against the historical baseline `cdf08544deea846bca4fa7e0c468ebee8d41e138` is empty. Start/end status showed only the same untracked current-round prompts; their contents were not read.

## Date
2026-10-03

## Axis
Safety. Independent, adversarial, peer-blind, read-only review.

## Verdict
**GO. Open findings: P0: 0; P1: 0; P2: 0; P3: 0.**

All three original Safety findings are closed as documentation defects. Their underlying runtime hazards remain.

## Prior-Finding Closure Table
| ID | Disposition claimed | Verified on corrected tree | Status |
| --- | --- | --- | --- |
| Safety P2-1 | Disclose validator bypass and completion-owner responsibility | Proposal `:71` and `:94`; draft `:77` explicitly distinguish ordinary outermost completion from `commit_only`. Executed characterization: `commit` rejected `-1`; `commit_only` published it without another validator call. | CLOSED: wording corrected; bypass unchanged |
| Safety P2-2 | Qualify healthy-state getters and fence contaminated-state reuse | Proposal `:119` and `:141`; draft `:118` and `:132` explicitly deny recovery by new transaction or discarded references. Executed characterization: inactive stale list remained visible; fresh getter did not enlist; assignment rejected the old token; current remained unchanged. | CLOSED: reuse warning corrected; cleanup limitation unchanged |
| Safety P2-3 | Separate preparation-time acceptance from reference publication/rollback | Proposal `:199`; draft `:139` explicitly disclose persistent acceptance and partially accepted maps. Executed characterizations: later freeze failure left the candidate accepted and current reference unchanged; map acceptance failure left an accepted prefix and unchanged current map. | CLOSED: effect boundary corrected; acceptance timing unchanged |

Closure combines corrected-text inspection with independent execution of the exact authorized recipe. It does not infer implementation repair from passing characterization assertions.

## Changed-Range Analysis
The two-document diff narrows decorator equivalence to the LCM adapter, removes the apparent selection of rewritable static, and corrects validation, cleanup, and owned-acceptance boundaries. The guide adds complete custom-key setup and clarifies `const` initialization defaults and explicit-alias prerequisites.

The characterization link and verification-limit wording support the dispositions. No object change outside those dispositions was identified. Constructor alias identity, completion cohorts, attachment boundaries, runtime implementation, and static outcome were not changed.

**NEW ARCHITECTURAL ROOT CAUSE: None established.**

## Evidence Base
- Read both complete corrected documents, `ManagedContextApiProposal-RemPlan-1.md`, and `ManagedContextApiProposal-Checks.md` at the pinned revision.
- Compared the object against the original reviewed revision; confirmed source, tests, repository instructions, and the listed lifecycle controlling references were unchanged.
- Rechecked transaction validation/completion and rollback loops, owned preparation resources, generated aggregate getters, repository `AGENTS.md`, and the pinned Pyrolyze lifecycle adapter.
- Retained the prior review’s controlling-plan analysis, including distinctions between historical intent and implemented behavior.
- Independently reran the exact inline shell command from Checks with `PYTHONDONTWRITEBYTECODE=1` and Python `-B`. It exited **0** and produced all four documented characterization observations.
- No files were written, no generation or arbitrary tests were run, and no git mutations or network calls were made. No current-round peer reports or prompts were inspected.

## Findings
No open findings. The original counterexamples remain reproducible, but the revised text now expressly describes them and withdraws the misleading guarantees that made them proposal defects.

## Invariant Analysis
Validation responsibility is now operation-specific. The text no longer implies that `commit_only` validates or that nested depth reduction publishes.

An inactive manager is explicitly insufficient evidence of participant cleanup. Healthy-state access rules are qualified, and contaminated-state reuse requires verified cleanup or supported recovery rather than an implicit retry.

Owned resource acceptance is explicitly separate from current-reference publication. Preparation failure and reference rollback are not represented as resource-effect undo.

Completion ownership, omitted-key expansion, joined nesting, independent multi-key completion, serialized access, shallow conversion limits, non-transactional fields, and live facades remain bounded. No additional promise of isolation, failure draining, graph-wide atomicity, or stronger publication guarantees was established.

## Risks And Next Action
The live decorator walkthrough remains unverified following the documented generation failure. The successful command exercised committed generated goldens and the live transaction runtime, not the live generation pipeline; it cannot substitute for that missing smoke verification.

Accept the corrected proposal for design review. L0/D4, resource-contract changes, constructor implementation approval, the static decision, and live-decoration-dependent integration retain their separate gates.
