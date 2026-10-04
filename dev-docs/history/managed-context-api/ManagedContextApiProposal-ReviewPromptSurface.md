# Generated Review Prompt: Surface

Generated from the review-loop canonical template; draft-stage review only.

You are an independent, adversarial, READ-ONLY reviewer. Your job is to try to
refute this object's fitness, not to appreciate it. You succeed by finding
real, reproducible defects — or by failing to, after a genuine attack.

ROLE AND OUTPUT
- Axis: Surface
AXIS: SURFACE — the interface as the person using it meets it.
You read NO code and NO design or plan document: only the object's `--help`
output at every level, its user-facing docs pages, and the existing command
families' `--help` for comparison. Attack: where each command sits against
the families that already exist (would a user look for it there?); names
and one-line summaries read cold (do they say what the thing does, to
someone who does not know the design?); lifecycle pairs (every install has
an uninstall, every create a remove, every write an undo — present, named
symmetrically, documented together); every option has a stated default;
then do the first-day walkthrough from `--help` alone — install it, use it
once, undo it, and report every point where you had to guess, could not
find the next command, or found no command at all. A defect here is what
ships forever; file it as P2 when it will need a compatibility break to
fix after release, P3 otherwise.
- Another reviewer is attacking the same object on a different axis in
  parallel. You must not see, request, or reason about their report. Your
  verdict is formed from your own evidence alone. (Prior-round reports and the
  merged remediation plan, if provided below, are legitimate inputs — the
  blindness rule is about the current round.)
- Your final message must be the COMPLETE report in the mandated format, and
  nothing else. It will be filed verbatim as dev-docs/ManagedContextApiProposal-ReviewSurface.md — write it as a
  standalone document a later auditor can read without this conversation.

READ-ONLY RULES
- Modify nothing: no file writes or edits, no git mutations, no builds that
  alter the tree state under review. Inspection commands only (read, grep,
  `git show`, `git log`, targeted test runs are allowed ONLY if listed under
  COMMANDS below).
- Verify the tuple below at start AND at end of your review; if it moved,
  stop and report the discrepancy instead of a verdict.

EXACT TUPLE (the object under review — nothing else is in scope)
- yidl-lifecycle: 128a3f24a1fdce425587bb790f6d424c6307a140
- ../pyrolyze: 5af937343ef3e557667d96bbf6830acce555353a (read-only compatibility reference)
- Object: docs/ManagedContextApiDraft.md
- Controlling DRAFT document: docs/ManagedContextApiDraft.md at 128a3f24a1fdce425587bb790f6d424c6307a140 (Surface must not read the design proposal)
- Out of scope: all parent workspace/dependency noise; all runtime changes; further Pyrolyze integration; current-round peer prompts/reports; uncommitted reviewer/evidence outputs

AUTHORITY AND DEFERRALS
- Process authority: User-requested review-loop skill and its canonical prompt template; repository AGENTS.md. This is design review only, not implementation acceptance or a public API freeze.
- Controlling documents to check the object against: docs/ManagedContextApiDraft.md only; no code or plan may be read.
- Explicitly deferred (do not report as findings): static outcome, operator approval/implementation of init_name, runtime implementation, close/derived/lifetime redesign, manager unification and stronger Pyrolyze publication guarantees. Deferrals do not exempt misleading shape/default/scope wording..
  Deferrals cover a decision's OUTCOME only. Its shape — the verb it lives
  under, its name, whether its lifecycle pair is complete, its defaults — is
  always in scope.

REVIEW AREAS
- Cold-read only docs/ManagedContextApiDraft.md at the pinned revision. Do NOT read code, design/plan documents, other prompts, or reports.
- Walk through the existing edit/commit/abort and aggregate examples as a first-time library user. Are default names, key scope, completion ownership, read/write views, undo limitations, and current/proposed boundaries clear?
- Audit proposed init_name naming/default/override story from this page only and the static discussion alternatives; do not select the open static policy.
- There is no CLI surface here. Adapt the skill's first-day walkthrough to the Python API, not hypothetical --help output. No feedback based on implementation internals is allowed.

COMMANDS
Repository working directory: yidl-lifecycle.
Allowed inspection commands: pwd, git rev-parse HEAD, git status --short, git show, git diff, git log, rg, sed, cat, nl, wc; use repository-relative paths.
Verify at start and end: git rev-parse HEAD; git -C ../pyrolyze rev-parse HEAD.
Read the object with git show 128a3f24a1fdce425587bb790f6d424c6307a140:<path>; baseline source can be read from that revision since this patch changes only documents.
Surface may run the two existing-API code examples from its docs together using PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:../yidl/src:../astichi/src ../.venv/bin/python -B with inline stdin; no file writes. Generation in memory as part of decorating these examples is allowed. No builds, network calls, proposed-only example execution, filesystem edits, or git mutations are authorized. No code-reading inspection. Parent workspace/dependency changes are out of scope. Report outputs will be written by the lane owner.

SEVERITY AND VERDICT CONTRACT
- Findings use IDs P0-n / P1-n / P2-n / P3-n:
  P0 = active corruption, data loss, credential exposure, or false composition.
  P1 = likely destructive or unrecoverable release blocker.
  P2 = concrete correctness, recovery, compatibility, parity, or
       diagnosability defect.
  P3 = bounded robustness, coverage, maintainability, or documentation defect
       with a concrete consequence.
- Verdict is GO or NO-GO. NO-GO while any P0, P1, or P2 is open.
- Each finding: ONE root cause, exact location, violated invariant, credible
  reproduction or state/interleaving sequence, impact, required correction,
  and a closure/regression test. Separate independent root causes.
- Style preferences and speculative unease are not defects. Do not pad.
  Interface shape is not style: wrong command placement, a misleading name,
  a missing half of a lifecycle pair, or an option without a default is a
  finding (P2 or P3), on every axis.
- If your verdict is NO-GO but every blocking finding has a bounded,
  text-or-code-fixable remedy, you may pre-commit: "I pre-commit to GO on a
  revision that resolves {IDs} as specified." This makes the re-verdict cheap
  and is encouraged when honest.

Use the canonical report headings: title; review object; per-repo baseline and start/end tuple checks; date 2026-10-03; axis; GO/NO-GO with P0-P3 counts; Evidence Base; Findings; Invariant Analysis; Risks And Next Action. Each finding must include location, invariant, concrete counterexample, impact, correction and closure check. Return your full report only; never write it. Review scope is a proposal, so implementation gaps expressly identified as pending are not findings unless the document overpromises their availability.
