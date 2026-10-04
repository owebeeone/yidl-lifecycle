# ManagedContext API Proposal: Remediation Round 1

Status: corrections submitted for independent re-verdict, not self-closed.

Original review tuple:

- `yidl-lifecycle`: `128a3f24a1fdce425587bb790f6d424c6307a140`.
- `../pyrolyze`: `5af937343ef3e557667d96bbf6830acce555353a`.

Reports are filed verbatim as `ManagedContextApiProposal-ReviewConsistency.md`,
`ManagedContextApiProposal-ReviewSafety.md`, and
`ManagedContextApiProposal-ReviewSurface.md` in this directory. Findings with
the same numeric ID on different axes are different findings.

## Dispositions And Closure Checks

| Finding | Disposition in the single documentation patch | Closure check |
| --- | --- | --- |
| Consistency P2-1 | Qualify decorator equivalence to the LCM adapter; explicitly distinguish the legacy decorator/markers | Compare both openings to adapter and legacy definitions at the pinned Pyrolyze revision |
| Consistency P3-1 | Remove the stale A2 statement selecting rewritable static | Compare A2, A5, implementation sequence and guide; all leave the static outcome open |
| Safety P2-1 | Qualify validation guarantee to outermost ordinary completion; document `commit_only` bypass and caller responsibility | Existing generated validator fixture rejects via `commit`, publishes via `commit_only` without an additional validator call |
| Safety P2-2 | Qualify healthy-state getters and explicitly fence stale-overlay/token reuse after interrupted cleanup | Earlier throwing rollback participant leaves later generated aggregate stale; inactive read exposes it, fresh getter does not enlist, assignment rejects token |
| Safety P2-3 | Distinguish owned acceptance during prepare from reference publication and rollback | Later freeze failure leaves unchanged current references and accepted candidate; owned-map failure leaves accepted prefix and unchanged current map |
| Surface P3-1 | Add complete custom-key manager/participant/scope setup | Cold reader can identify all setup calls from guide alone |
| Surface P3-2 | State `const`'s `init=True` default and explicit-alias versus omitted-alias rule | Cold reader can establish the example's validity and `init=False` omission behavior |

No findings are disputed. Original reports remain unedited. The proposal does
not change its API spelling, constructor alias resolution, implementation
scope, runtime behavior, mutation boundary, static outcome, or Pyrolyze
compatibility policy. Continue the same reviewers for focused closure checks.

## Characterization Evidence And Limits

The reproducible inline command in `ManagedContextApiProposal-Checks.md`
passes all four existing-behavior characterizations. It loads committed generated
source goldens, supplies their existing fixture data, and uses the live
transaction runtime. It does not regenerate artifacts or modify source/tests.

The Surface review's live decorator walkthrough did not run: decoration failed
before assertions with a missing `build_lifecycle_class`. A separate read-only
probe found the generated executable module contained only `Pass`. This remains
an explicitly unverified live-pipeline smoke test, not evidence of API success
or a defect fixed by this patch. Investigate before resuming implementation
that relies on live decoration. Do not edit runtime code in this document loop.

Review acceptance is limited to the corrected proposal and user-facing draft;
it cannot close L0/D4 or approve the deferred constructor/static decisions.
