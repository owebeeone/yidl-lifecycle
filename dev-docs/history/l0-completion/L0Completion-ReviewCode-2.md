# L0 completion library checkpoint — Code-AXIS REVIEW (Remediation 1 Re-Verdict)

**Review object:** `yidl-lifecycle` at `4b86eec179942d96012aa4a1d92752a34cae87ef`, L0-1/L0-2 manager/generated-library checkpoint. Corrected candidate reviewed against `pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md` at the settled Pyrolyze SHA. Status: library-only review, 2026-10-08.

**Baseline:** Lifecycle baseline `371dfa530a975c27f7a6c09a7648f7f00532ab29`; previously reviewed candidate `30b7c83f3ef7a733a38a55b221a022aa7b7f8e84`. Companion HEADs:
- `pyrolyze`: `ac410240fc33459da31ffcc87863f915ed7e124e`
- `yidl`: `a7cc1de7b630b55bd194940ecad83f3f1738cf8a`
- `astichi`: `1c47f781d3804130fdd61cbee07a3b2e4529158a`

Sources were inspected through `git show`, the remediation diff, and numbered working-tree reads. HEADs were verified at both boundaries.

**Date:** 2026-10-08  
**Axis:** Code: interface contracts, ownership, call graphs, compatibility, and error provenance. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on its current-round report. Filed verbatim by the lane owner.

**Verdict: GO** — Original Code finding P2-1 is CLOSED. No new findings were identified in the bounded remediation.

---

## 0. Evidence Base

Read the local review-loop `SKILL.md`, parent and relevant repository `AGENTS.md`, the controlling L0 plan, and these lifecycle documents: `dev-docs/L0Completion-RemPlan-1.md`, `dev-docs/TransactionScopeOwnership.md`, and `dev-docs/L0CompletionVerification.md`, including its appended corrected-candidate verification.

Inspected the prior-candidate-to-corrected-candidate diff, concentrating on:
- `src/yidl_lifecycle/transaction_yidl.py:126-151,254-533,597-780,822-940`: original metadata, completion authority, failure retention, validation fencing, scopes, and dispatch.
- `src/yidl_lifecycle/yidl/lifecycle_core.yidl:338-345` and `lifecycle_managed.yidl:517-524`: both declarative hook wrappers and their generated counterparts.
- `tests/test_transaction_yidl.py:1016-1140`: hostile annotation, scope draining, metadata mutation, and replacement-token regressions.
- `tests/data/gold_src/yidl_transactional_completion_failures.py:205-228,306-329,422-446` and `yidl_transactional_lifecycle_core.py:146-179,233-260`, with checked-in generated outputs.
- `pyrolyze/src/pyrolyze/runtime/context_state_lcm/render_attempt.py:169-265` and the accepted SC3 caller audit: actual validation/completion ordering and pending consumer transition.

Executed, without writing files:
- The authorized native manager command: `116 passed`.
- The exact original P2-1 counterexample against both the prior manager loaded from `git show` and the corrected manager: prior failure reproduced; corrected drain and exception identity passed.
- Both canonical fixtures through in-memory `runpy`, `render_case()`, and `validate_case()`, under native and Python lowering. All six completion-fixture artifacts and four core-fixture artifacts matched exactly in each backend. Read-only complete decorator-to-YIDL consistency also passed.
- Additional probes for hostile `KeyboardInterrupt` annotation, `BaseExceptionGroup` identity/order, and direct group-manager legacy dispatch with nested begin and equal-but-nonidentical requested keys: passed.

Boundary verification found all four HEADs unchanged. Lifecycle, YIDL, and Astichi remained clean. Pyrolyze contained only the two explicitly excluded untracked documents; their contents were not read.

## 1. Prior Finding Closure

| Finding | Original Counterexample and Result | Changed Enforcement | Disposition |
|---|---|---|---|
| P2-1: Diagnostic annotation aborts completion draining | Participant A’s prepare raises an original exception whose overridden `add_note()` raises `RuntimeError`. The prior candidate stops after `prepare:A`, omits cleanup, and exposes the annotation failure. The corrected candidate discards A and B, runs both rollback notifications, rethrows the original exception by identity, retains it in completion evidence, and finalizes ownership correctly. | `transaction_yidl.py:293-309` retains before guarded standard `BaseException.add_note`; validation at `389-399` and multi-key scopes at `765-774` follow the same rule. Core YIDL `338-345` and managed YIDL `517-524` append first and guard standard annotation. Generated artifacts match their sources. | **CLOSED**. Exact prior/corrected probe passed; all 116 manager cases passed; complete and core canonical runtime and exact-artifact checks passed under both backends. |

No new findings.

## 2. Invariant Analysis

- **Original errors remain authoritative.** Annotation overrides, malformed note storage, and failing diagnostic formatting cannot replace the retained failure or interrupt draining. The system-exception probe preserved the original `KeyboardInterrupt` as the first `BaseExceptionGroup` leaf alongside a later rollback failure.

- **Metadata corrections preserve dispatch while removing relabel authority.** Creation-time key/id values feed callbacks, diagnostics, and completion records. Public metadata mutation fails authority checks; replacement transactions are not finalized accidentally. Direct group-manager probes preserved legacy `(id, key)` callback order, optional callback behavior, nested completion returning `None`, and final integer returns.

- **Validation cannot borrow a completion write window.** Same-key public validation now encounters the completing fence before invoking validators. The complete fixture exercises before-hook validation reentry without running validators or materializing factories. Standalone and independent-key validation remain supported. Pyrolyze’s inspected caller validates before `commit_only()`, so this guard does not introduce an unrelated call-order break.

- **Both generated hook paths actually drain.** Complete canonical coverage exercises inherited/local grouping and later participants. The extended core-only fixture selects its generated wrapper. Original exception identity, direct references, notification failures, and terminal evidence survive both paths; runtime and exact-source comparisons passed.

- **The patch remains bounded.** Preparation stopping, publication/discard eligibility, and original failure traces continue to pass the manager suite. The corrections do not add markers, key syntax, enums, saved copies, current-value undo, cross-key atomicity, compiler changes, or consumer activation.

## 3. Risks and Next Action

The recorded full-version matrix and historical Pyrolyze results are documentary evidence, not reruns in this review. The pre-existing Python/native owned-field hygienic-name discrepancy remains an explicitly failing exact-source comparison; it is not counted as passing. The two documented Pyrolyze consumer-transition failures remain pending adoption work outside this checkpoint.

Next action: the lane owner should combine this Code GO with the independently produced State re-verdict at this exact tuple. This verdict accepts the bounded library remediation only; it does not authorize Pyrolyze adoption or live activation.
