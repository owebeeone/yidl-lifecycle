# ManagedContext API Proposal: Review Loop

## Acceptance Scope

Status: **accepted at yidl-lifecycle `432a61b18021912783267f2ed677208d77802cd1`
and ../pyrolyze `5af937343ef3e557667d96bbf6830acce555353a` after
`ManagedContextApiProposal-ReviewConsistency-1.md`,
`ManagedContextApiProposal-ReviewSafety-1.md`, and
`ManagedContextApiProposal-ReviewSurface-1.md` reported GO; this accepts the
corrected proposal and user-facing draft as a reviewable design only**.

Acceptance does not implement or approve constructor aliases, settle static,
freeze a released API, certify live generation, close L0/D4, or change the
accepted Pyrolyze integration scope. The proposal remains an operator-facing
DRAFT with those choices open.

Reviewed files:

- `dev-docs/ManagedContextApiProposal.md`.
- `docs/ManagedContextApiDraft.md`.

The evidence commit after this acceptance adds only re-verdicts, generated
re-verdict prompts, and this ledger. The reviewed files' bytes are unchanged.

## Process And Revision Ledger

The user requested the review-loop skill. The lane owner drafted the object;
three independent reviewers had fresh contexts, inherited model selection,
and read-only authority. Consistency and Safety were peer-blind; Surface read
the user-facing page rather than the design/code. Same reviewers performed
focused re-verdicts after one merged documentation remediation.

| Stage | yidl-lifecycle revision | Result |
| --- | --- | --- |
| Source baseline | `cdf08544deea846bca4fa7e0c468ebee8d41e138` | Runtime/tests/goldens unchanged throughout this loop |
| Original draft | `128a3f24a1fdce425587bb790f6d424c6307a140` | Consistency NO-GO; Safety NO-GO; Surface GO with P3 findings |
| Remediation 1 | `432a61b18021912783267f2ed677208d77802cd1` | All three GO; no open P0/P1/P2/P3 |

Remediation rounds used: **1 of at most 2**. No new architectural root cause
was identified in re-review. No disputed findings or silently skipped findings.

## Findings By Discovery And Closure

| Axis | Initial P0 | P1 | P2 | P3 | Final open findings |
| --- | --- | --- | --- | --- | --- |
| Consistency | 0 | 0 | 1 | 1 | 0 |
| Safety | 0 | 0 | 3 | 0 | 0 |
| Surface | 0 | 0 | 0 | 2 | 0 |

The four initial blocking defects were overbroad legacy/YIDL decorator
equivalence, undisclosed `commit_only` validation bypass, unconditional
inactive-working-view claims after broken cleanup, and omitted preparation-time
owned acceptance effects. Three documentation defects concerned a stale static
summary, custom-key setup, and the alias example's `init` default.

All dispositions and closure checks are in
`ManagedContextApiProposal-RemPlan-1.md`. Original reports are filed verbatim;
re-verdicts independently close their own findings. There was no independently
reported same-root-cause convergence in the initial findings, so none is claimed.

## Verification And Limits

- The four inline failure characterizations in
  `ManagedContextApiProposal-Checks.md` passed when run by the lane owner,
  including rerunning the documented recipe. Safety independently reran them
  successfully; Consistency inspected rather than executed them.
- These checks use committed generated goldens with the live transaction runtime.
  They are observations of current hazards, not fixes or duplicate permanent
  success tests.
- Surface's live decorator walkthrough failed before assertions because
  `build_lifecycle_class` was absent. The read-only AST probe produced only
  `Pass`. No root cause was established or repaired in this loop.
- The live generation walkthrough is therefore **not verified**. It must be
  investigated before live-decoration-dependent implementation proceeds.
  Successful golden-based characterizations do not substitute for it.
- Whitespace validation and the machine-specific-path scan passed for authored
  documents/prompts. No runtime, test, or golden file was modified.
- Pyrolyze stayed clean at its pinned revision. Parent workspace changes and
  dirty dependency work were outside scope and left untouched.

## Operator Decisions Still Open

1. Discuss static: lazy/write-once, lazy ordinary rewritable storage, and an
   invalidatable computed cache are distinct semantics. Do not choose by
   interpreting a contradictory historical document as approval.
2. Decide whether constructor-only `init_name` is worthwhile under A4's naming,
   inheritance, and provider-identity rules.
3. Select whether approved library changes precede I3a or run separately.
   Neither choice authorizes new manager sharing, outer publication guarantees,
   resource-lifetime redesign, or implicit graph attachment.

Only document-review commits were made on `lcm-resume`. No tags, push, merge,
parent submodule-pointer commit, or implementation activation was performed.
