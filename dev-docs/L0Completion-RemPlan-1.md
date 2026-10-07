# L0 Completion Remediation 1

Status: bounded remediation of candidate
`30b7c83f3ef7a733a38a55b221a022aa7b7f8e84`; not implementation acceptance.

The [Code review](L0Completion-ReviewCode.md) and
[State review](L0Completion-ReviewState.md) independently converged on the
diagnostic-annotation failure. State also identified validation-window reentry
and token-metadata relabeling. All three are accepted findings, not disputed.

## Dispositions

| Finding | Correction | Closure Coverage |
| --- | --- | --- |
| Code P2-1 / State P2-1 | Retain original errors before diagnostic annotation; formatting and annotation are best-effort. Invoke the standard exception annotation implementation, not a user override; guard malformed notes and diagnostic formatting. Apply to manager, validation, scopes, and both generated hook paths. | Narrow manager prepare/discard/validation/scope errors with hostile annotation; canonical inherited commit/rollback hooks prove child and later-participant draining. |
| State P2-2 | Reject same-key public validation while final completion is in progress. Ordinary standalone validation and other-key operations keep their existing rules. | Canonical before-hook validation reentry with existing/untouched candidate writers and materializing getters; reject before their side effects, discard coherently, preserve permitted direct before-hook staging. |
| State P2-3 | Preserve original key/ID independently of mutable public metadata; capture them for the completion session. Use them for callbacks, diagnostics, evidence, and results. Metadata changes are detected as authority loss, not silently certified. | Narrow key/ID relabeling before/during prepare and after actions; original record identity, fail-closed authority, monotonic following IDs, and untouched replacement tokens. |

No marker, key syntax, callback protocol, savepoint, current-value undo,
compiler change, live activation, or resource-admission change is included.

## Sequence

1. Add narrow failure tests and extend the existing canonical failure fixture.
   Confirm the original counterexamples fail on the reviewed candidate.
2. Implement one combined manager/YIDL correction; regenerate the complete
   decorator, all goldens, and constructor fixture from owning sources.
3. Rerun focused checks, full supported native matrix, Python canonical checks,
   and decorator consistency. Preserve the known owned-field Python source
   difference and the two pending historical Pyrolyze transition cases.
4. Commit the corrected candidate. Continue the same two reviewers with this
   plan and the revised exact tuple; each reruns or retraces its original
   findings. The implementer does not self-close the findings.

The mutation/permission contract is unchanged: the correction enforces the
already accepted boundary. If remediation requires changing that contract or
reveals another architectural assumption, stop and reassess before widening.
