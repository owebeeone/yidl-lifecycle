# ManagedContext API Proposal: Consistency Review

## Review Object
`dev-docs/ManagedContextApiProposal.md` and `docs/ManagedContextApiDraft.md` at `128a3f24a1fdce425587bb790f6d424c6307a140`. The proposal is the controlling DRAFT. This verdict concerns design consistency, not implementation acceptance or operator approval.

## Per-Repo Baseline And Tuple Checks
| Repository | Required Baseline | Start | End |
| --- | --- | --- | --- |
| `yidl-lifecycle` | `128a3f24a1fdce425587bb790f6d424c6307a140` | Exact match | Exact match |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Exact match | Exact match |

The tuple remained unchanged. Comparison with the proposal’s source baseline, `cdf08544deea846bca4fa7e0c468ebee8d41e138`, confirmed that only the two review-object documents changed.

## Date
2026-10-03

## Axis
Consistency. Independent, adversarial, read-only review; no current-round peer prompts or reports consulted.

## Verdict
**NO-GO.** Open findings: P0: 0; P1: 0; P2: 1; P3: 1.

## Evidence Base
- Inspected both objects using `git show` at the pinned revision.
- Checked `AGENTS.md`, `dev-docs/YidlTransactionalYidlPhaseF-1Plan.md`, `dev-docs/YidlPyroCloseTheGapPlan.md`, `dev-docs/YidlLifecycleFieldKindMatrix.md`, `dev-docs/YidlPyrolyzeLifecycleParityPlan.md`, and the pinned `../pyrolyze/dev-docs/PytoLifecyleIntegPlan.md`.
- Cross-checked markers, harvesting/inheritance metadata, transaction management, core/managed/transient lowering, factory lowering, const/static/local-store resources, and canonical fixtures.
- Checked pinned Pyrolyze legacy decorator behavior, LCM decorator aliases, and construction-before-attachment source.
- No writes, builds, generation, tests, network calls, or Git mutations. Counterexamples below are source-derived, not executed.

## Findings

### P2-1: Decorator Equivalence Is Asserted Beyond The LCM Alias
**Location:** `dev-docs/ManagedContextApiProposal.md:12-14`; `docs/ManagedContextApiDraft.md:6-7`.

**Invariant:** An existing-API equivalence claim must identify the actual import boundary. Distinct implementations and incompatible marker surfaces cannot be presented as interchangeable.

**Concrete counterexample:** The draft says verbatim: “they are the same decorator, not two implementations.” At the pinned compatibility revision, `../pyrolyze/src/pyrolyze/runtime/context_state_lcm/lifecycle_adapter.py:8` aliases the library decorator, but `../pyrolyze/src/pyrolyze/lifecycle.py:3939-3955` defines a separate legacy `managed_context`. Replacing the guide’s `lifecycle` decorator with that legacy import while retaining its YIDL markers fails: legacy declaration collection accepts `LifecycleField`, not `LifecycleMarker`, and raises `TypeError` for the public `name` declaration (`../pyrolyze/src/pyrolyze/lifecycle.py:3797-3816`).

**Impact:** The existing-API explanation falsely implies import/marker compatibility. It also obscures the distinction required by the parity plan’s separate legacy and YIDL implementation baselines.

**Correction:** Qualify both statements: Pyrolyze’s LCM runtime uses a local alias for `yidl_lifecycle.lifecycle.lifecycle`; `pyrolyze.lifecycle.managed_context` remains a separate legacy implementation. No runtime migration or legacy removal is required.

**Closure Check:** Re-read both openings against the pinned adapter import and legacy definition. The documented equivalence must apply only to the LCM alias, and must not imply that the legacy decorator accepts the guide’s markers.

### P3-1: A2 Mislabels An Unselected Static Alternative As The Proposal
**Location:** `dev-docs/ManagedContextApiProposal.md:127`.

**Invariant:** Summary tables must preserve the controlling decision status, especially where behavior remains explicitly unresolved.

**Concrete counterexample:** A2 states verbatim: “currently write-once, A5 proposes rewritable”. But A5’s decision row at line 57 requires retaining current behavior meanwhile; lines 258-261 classify its options as discussion alternatives; and `docs/ManagedContextApiDraft.md:129-134` explicitly denies a selected replacement change.

**Impact:** A reader deriving scope or acceptance criteria from the facade table receives a different target from the decision section and user-facing draft.

**Correction:** Replace the row’s proposal wording with “currently write-once; replacement policy remains unresolved under A5.”

**Closure Check:** Compare the A2 row, A5 classification/options, implementation sequence step 4, and user-facing static paragraph. All must describe rewritable storage as unselected, without changing runtime or rejection goldens.

## Invariant Analysis
- Explicit-key examples, manager-wide delegation, omitted-key defaults, nested joins, and independent multi-key completion agree with the inspected source.
- Live facades, plain-field sharing, const reference immutability, and shallow freeze/thaw limitations are consistent with the lowering.
- A4 separates constructor spelling from field/provider identity and specifies defaults, override inheritance, resolved-name collision checks, and legacy-metadata fallback. Pending implementation is not treated as a defect.
- A6 preserves I1b construction-before-attachment and holder-first manager/completion boundaries. L0/D4 remains conditional; existing failure-loop defects are acknowledged rather than falsely certified fixed.
- No completed supersession list is claimed: static reconciliation is conditional future work. No additional controlling-document contradiction was established.

## Risks And Next Action
Resolve P2-1 before accepting the proposal; repair P3-1 in the same documentation revision. Preserve all operator deferrals and existing runtime boundaries.

I pre-commit to GO on a revision that resolves {P2-1, P3-1} as specified.
