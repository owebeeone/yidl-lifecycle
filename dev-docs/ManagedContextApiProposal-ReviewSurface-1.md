# ManagedContext API Draft: Surface Review, Round 1

## Review Object
`docs/ManagedContextApiDraft.md` in `yidl-lifecycle` at `432a61b18021912783267f2ed677208d77802cd1`.

This is a user-facing proposal review, not implementation acceptance or an API freeze.

## Baselines And Tuple Checks
| Repository | Required Baseline | Start | End |
|---|---|---|---|
| `yidl-lifecycle` | `432a61b18021912783267f2ed677208d77802cd1` | Matches | Matches |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Matches | Matches |

Both tuple checks used the prescribed `git rev-parse` commands. Neither revision moved. No files were written or Git state mutated.

## Date
2026-10-03

## Axis
Surface: cold-read Python API documentation, defaults, lifecycle boundaries, and first-day walkthrough. No CLI exists for this object.

## Verdict
**GO** — Open findings: P0: 0, P1: 0, P2: 0, P3: 0.

## Prior-Finding Closure Table
| ID | Disposition claimed | Verified on corrected tree | Status |
|---|---|---|---|
| P3-1 | Supply custom-key manager setup | Lines 53–69 show `managed(EDITS, ...)`, `TransactionManager(tx_keys=(EDITS,))`, participant construction, scope entry, and committed-value inspection | Closed by documented walkthrough |
| P3-2 | State the alias prerequisite’s default and applicability | Lines 162–168 state `const` defaults to `init=True`, restrict explicit non-`None` aliases, and explain `init=False` with default `init_name=None` | Closed by documented walkthrough |

Closure was verified by reading the pinned document through inspection commands. Neither corrected example nor proposed behavior was executed; these are documentation closures, not implementation claims.

## Changed-Range Analysis
The draft-only diff from `128a3f24a1fdce425587bb790f6d424c6307a140` adds the custom-key recipe and clarifies the constructor-alias defaults, directly addressing both prior findings.

Additional changes outside those two dispositions distinguish the legacy Pyrolyze decorator, explain validator bypass through `commit_only`, qualify healthy-state working access, and disclose interrupted-cleanup and owned-resource rollback limitations.

These additions were reviewed independently as surface wording. They do not promise recovery, atomic resource rollback, or implementation of proposed aliases. No new architectural root cause was established. The design proposal and remediation plan were not read.

## Evidence Base
- Read pinned repository `AGENTS.md` and the complete numbered user-facing draft.
- Inspected only `docs/ManagedContextApiDraft.md` in the revision diff.
- Retraced both original counterexamples against the corrected text.
- Rechecked normal completion, exception-driven abort, aggregate editing, view semantics, alias inheritance, and the open static alternative.
- The previous authorized executable walkthrough failed at the first decorator with `LifecycleDefinitionError: Counter: lifecycle class build failed: 'build_lifecycle_class'`, before any assertions. It was not rerun this round and remains unverified.
- No implementation source, evidence implementation, current-round peer prompt, or peer report was inspected.

## Findings
No open findings. Both prior P3 documentation defects are closed; no additional reproducible surface defect was established.

## Invariant Analysis
- **Setup and key scope:** The custom-key path now supplies the previously missing manager configuration. Examples use explicit keys; manager-wide completion and independent multi-key completion remain disclosed.
- **Completion and cancellation:** Normal scope exit commits; an exception demonstrates abort. The page explicitly shows that plain-field writes survive abort and warns that publication and resource acceptance are not generally reversible.
- **Views and aggregates:** Overlay, committed, and working views are distinguished. Live views, shallow conversions, retained mutable references, and stale-state limitations are stated.
- **Defaults and overrides:** The alias example’s `init` prerequisite no longer requires guessing. Effective constructor naming, property/provider separation, inheritance, duplicate rejection, and inherited-renaming rejection are documented.
- **Availability:** Existing imports are separated from legacy Pyrolyze markers. Constructor aliases remain explicitly unavailable.
- **Static policy:** Current write-once behavior and the possible replacement alternative remain distinct. No reset, invalidation, or recomputation policy was inferred or selected.

## Risks And Next Action
The verdict covers document fitness only. Executable examples remain unverified because the prior run failed before assertions; rerun them in a supported working environment before treating the page as execution-validated.

No further Surface remediation is required for the two prior findings. Runtime recovery guarantees and the open static decision remain outside this verdict.
