# ManagedContext API Draft: Surface Review

## Review Object
`yidl-lifecycle` document `docs/ManagedContextApiDraft.md` at `128a3f24a1fdce425587bb790f6d424c6307a140`. This is proposal review, not implementation acceptance or an API freeze.

## Baselines And Tuple Checks
| Repository | Required Baseline | Start | End |
|---|---|---|---|
| `yidl-lifecycle` | `128a3f24a1fdce425587bb790f6d424c6307a140` | Matches | Matches |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Matches | Matches |

Both revisions remained unchanged. Working-tree status was unchanged; uncommitted review artifacts were excluded and unread. No files were written.

## Date
2026-10-03

## Axis
Surface: cold-read Python API documentation and first-day walkthrough. No implementation source, design proposal, plan, or current-round peer report was read.

## Verdict
**GO** — P0: 0, P1: 0, P2: 0, P3: 2.

The findings require bounded documentation corrections, not compatibility-breaking API changes.

## Evidence Base
- Read the pinned draft using `git show`; locations below use its numbered lines.
- Read repository `AGENTS.md`.
- Executed the two existing-API examples together using the authorized bytecode-disabled, inline Python invocation.
- Execution stopped at the first `@lifecycle` decoration with `LifecycleDefinitionError: Counter: lifecycle class build failed: 'build_lifecycle_class'`. No example assertions were reached. This establishes a verification limitation, not an in-scope implementation finding.
- No CLI exists for this object. Installation prerequisites are assumed by the page; use and cancellation were assessed through its Python examples.

## Findings

### P3-1: Custom-Key Setup Has An Undocumented Prerequisite
**Location:** `docs/ManagedContextApiDraft.md:46–54`.

**Invariant:** A documented transaction-key choice must provide enough public API instructions to establish its required manager configuration.

**Concrete counterexample:** A reader changes `managed(default=0)` to `managed("edits", default=0)` as instructed. The next sentence requires the supplied manager to “know that key,” but the page supplies neither constructor syntax nor a registration operation for doing so. The reader cannot complete that setup from this page without guessing or consulting another source.

**Impact:** The documented nondefault-key path is not self-contained. Readers cannot establish its prerequisite before attempting an edit.

**Correction:** Add a minimal existing-API example showing how to configure a manager for a custom key, construct its participant, and enter the corresponding scope.

**Closure check:** A fresh reader can follow that example using only the page and identify the exact setup and scope calls without inventing an operation.

### P3-2: The Alias Example Depends On An Unstated `init` Default
**Location:** `docs/ManagedContextApiDraft.md:118–125`.

**Invariant:** A proposed option’s stated preconditions and defaults must make its example interpretable without prior marker knowledge.

**Concrete counterexample:** The proposed declaration is `const(init_name="slot_id", default=None)`. The text then says `init_name` requires `init=True`, but neither the example nor the page states the default of `init`. A cold reader must assume that omission satisfies the required condition.

**Impact:** The reader cannot determine from the page alone whether its sole proposed alias example meets its own precondition. The `init_name` default is documented; the prerequisite’s default is not.

**Correction:** State the applicable marker’s `init` default explicitly. Also clarify whether the `init=True` requirement applies to explicitly supplied aliases or to the automatically defaulted constructor name.

**Closure check:** A documentation-only walkthrough can explain why the shown declaration is valid and what happens for an `init=False` declaration with no explicit alias, without consulting implementation or choosing the deferred implementation outcome.

## Invariant Analysis
- The default transaction symbol, normal-exit commit, and exception-driven abort appear together. Manager-wide completion ownership and independent multi-key completion are disclosed.
- The scalar example distinguishes pending from committed values and explicitly demonstrates that abort does not restore plain fields.
- Aggregate editing directs readers to `.working`, states its outside-transaction behavior, and warns about shallow conversions and retained mutable references.
- Live-view behavior, shared nontransactional storage, and nonrecursive `const` protection are explicit.
- Proposed aliases are clearly unavailable today. Property/provider names, inherited aliases, duplicate names, and inherited-renaming rejection are stated.
- Static replacement remains an open alternative. Reset, invalidation, and recomputation are explicitly excluded from that alternative; no deferred policy was selected.
- No additional blocking surface defect was established.

## Risks And Next Action
Resolve P3-1 and P3-2 with documentation edits. The suggested initvar/copying-factory fallback would also benefit from a directly usable example.

The executable walkthrough remains unverified because decoration failed before either example ran. Recheck those examples in a working supported environment; diagnosis of that failure belongs outside this Surface review.
