# End-user documentation specification

Date: 2026-10-29. Scope: Lifecycle first, with reusable principles for Dataclass
and Undoable. The user authorized creation of the Lifecycle documentation after
this specification. This is a content specification, not an API redesign.

## Outcome and boundary

A Python programmer must be able to choose the library, install it, build and
adapt a realistic model, predict its behavior, and diagnose common mistakes
without learning the YIDL compiler or reading implementation files.

Editable components are Lifecycle's README, public documentation, supporting
executable examples, and this specification/index. Library implementation,
generated builders, packaging, release workflows and dependencies are
reference-only. Dataclass, Undoable and YIDL are reference-only for this pass.
No API changes, dependency upgrades, releases or documentation-site framework
are prerequisites. Developer and experiment evidence must be preserved.

Python's [dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
is a benchmark for specificity: explain parameters, defaults, interactions and
consequences with examples. Its organization is not a required template.

## Audience and opening

Assume familiarity with Python classes, decorators, functions and exceptions.
Do not assume knowledge of transactions, facades, generated code or YIDL.
Serve both sequential learners and returning readers looking up one operation.

Lifecycle's opening promise is: **try changes to managed fields, then keep or
discard them together**. Immediately demonstrate that benefit. Explain the
transaction manager as the object that controls the edit boundary. Do not lead
with compiler architecture, dependency qualification, review verdicts or cost.
Do not imply database persistence, concurrent isolation or reversal of arbitrary
side effects. Ordinary fields do not participate in rollback.

## Learning evidence and editorial choices

These findings inform the design; none establishes the optimal documentation
for these libraries or a guaranteed retention improvement.

- [Chi et al. (1989)](https://doi.org/10.1207/s15516709cog1302_1)
  studied explanations produced while learning mechanics examples. Better
  explanations connected steps to principles. Application here: explain why
  committed and pending values differ, and offer a short optional prediction
  or explanation prompt at important boundaries.
- [Karpicke and Roediger (2008)](https://learninglab.psych.purdue.edu/downloads/2008/2008_Karpicke_Roediger_Science.pdf)
  found a delayed-recall benefit from repeated retrieval in vocabulary learning.
  Application here: offer a small adaptation task with an immediate answer;
  do not assume copying a snippet proves understanding.
- The [IES practice guide (2007)](https://ies.ed.gov/ncee/wwc/PracticeGuide/1)
  recommends spacing, alternating worked examples with problems, connecting
  concrete and abstract representations, and explanatory questions. Application
  here: pair runnable examples with state tables and revisit a small number of
  invariants in later tasks. Cross-links permit later revisiting; they do not
  themselves constitute experimentally controlled spaced practice.

An independently consulted Astra agent recommended an immediate useful result
followed by a revealing contrast: commit, rollback, live views, then an ordinary
field that survives rollback. It also recommended a direct reference route for
experienced readers. Its advice is editorial judgment, not empirical validation.

Use complete examples before adaptations, keep explanations beside the relevant
code, and grow the introductory model gradually. Avoid mandatory quizzes,
withheld answers, artificial suspense, learning-style claims and forced reading
order. Documentation must be easy to use even when readers remember little.

## Content architecture

| Destination | Reader's question | Required content |
| --- | --- | --- |
| README | Is this useful to me? | Benefit, installation, small working example, next destinations, concise compatibility/licensing, contributor link |
| Start here | Can I make my first edit? | Complete imports, construction, successful commit, rollback, expected output |
| Concepts | What values am I looking at? | Manager/key boundary, managed versus ordinary fields, current/working/default, live views, state table |
| Task guides | How do I do this job? | Collections, multiple objects/keys, factory dependencies/lazy fields, validation/hooks, resources/recovery |
| Field reference | Which declaration and options? | Every supported marker, signatures/defaults, provider rules, mutability, conversion and comparison semantics, errors |
| Transaction reference | What does each operation promise? | Begin/completion, scope behavior, return values, nesting, callbacks, completion evidence and concurrency limits |
| Troubleshooting | Why did this happen? | Symptom, cause, corrective action and links; current installation/support facts |
| Advanced reference | What are the lifetime/cache limits? | Keep detailed ownership/cache material accessible without making it onboarding |

Tutorial route: successful scalar edit → failed edit → committed/pending values
and retained live views → ordinary-field contrast → editable collection → shared
objects and joined scopes → named factories → hooks and resources. Independent
guides must state prerequisites and offer complete runnable specimens.

## Required semantic coverage

- Managed writes need the matching active transaction; committed values remain
  readable while edits are pending. Scope success commits, exception rolls back.
- Live views do not pin history. Plain fields, lazy values and scratch storage
  are nontransactional. `const` prevents replacement, not deep mutation.
- Working aggregate access initiates thawing; ordinary reads do not. Shallow
  tuple/list conversion does not isolate mutable elements. Escaped working
  references must not be reused after completion.
- Shared manager/key completion covers enlisted objects. Nested same-key scopes
  join, not savepoints. Independent keys are not an atomic multi-key group.
- Factory parameters request named providers. Factories initialize, not reactive
  formulas. Explain supplied overrides, `init=False`, `initvar`, class/instance
  providers, lazy timing and transaction-local transient factories.
- Validation may reject preparation. After-hook errors can occur after
  publication. Resource acceptance and external effects are not reversed merely
  because a reference is rolled back. Explain completion evidence for recovery.
- Describe supported imports and actual signatures, not proposals. Keep legacy
  `static` alias and unavailable constructor aliases clearly distinguished.
- State support qualification precisely; do not certify untested platforms or
  backends. Present cache controls as optional operational guidance.

## Example and reference rules

Runnable specimens use published APIs, deterministic assertions and observable
output. Tutorial code is checked against the repository implementation with the
documented backend, with no sibling-source requirement in user installation
instructions. Small snippets may build on an explicitly named earlier example;
label continuations. Do not present incomplete fragments as standalone scripts.

Each reference entry must state purpose, accepted parameters/defaults, return
behavior, relevant exceptions and interactions. Shared options can be described
once and linked locally. Explain field policy beside its declaration. Keep
advanced restrictions near the operation they constrain. Preserve existing links
with compatibility pages/anchors where practical.

## Acceptance and evaluation

Mechanical acceptance: all linked local files/anchors resolve; standalone Python
examples and complete tutorial blocks run and produce their documented results;
signatures agree with implementation; no implementation/configuration changes;
historical developer evidence remains accessible. Use existing coverage and a
focused documentation execution check rather than duplicating success tests.

Editorial acceptance: opening states a concrete benefit and boundary; readers
can answer what commit, rollback, live views and joined nesting do; all field
kinds and options are discoverable; supported behavior is separate from proposals;
reference readers can bypass teaching exercises. Automated checks establish
example correctness, not learning effectiveness.

For later usability evaluation, observe representative Python programmers doing
three tasks: run an edit, adapt it to another model, and diagnose an ordinary-field
rollback mistake. Record completion, assistance needed and incorrect predictions.
Optionally repeat a prediction/adaptation task after a delay to explore retention.
No reader study has been performed; do not report a retention gain or an optimal
psychological hook as measured fact.

## Later consumers

Apply the same depth and quality checks, with separate starting stories:
Dataclass teaches single-state models, conversion/validation, initialization and
permanent optional freeze; Undoable teaches edit → undo → redo, roots/frames,
live handles versus snapshots and discarded redo branches. Neither requires
reading Lifecycle first. Their exact field APIs must be checked separately.

## Lifecycle delivery verification

The README, learning path, task guides, field/transaction reference,
troubleshooting and seven runnable examples were created from this spec.
Compiler/dependency detail moved into a contributor guide; existing ownership,
cache, proposal and developer/experiment records remain available. The previous
transaction-guide URL and headings were retained for incoming links.

Checks on 2026-10-29 used CPython 3.14.3 with the Python backend and persistence
disabled. Seven example scripts and fourteen Python blocks in the README/new
guides passed, including the tutorial's printed-output comparison. The same
examples and fourteen blocks also passed with this checkout's Lifecycle source
against installed released dependencies. Local file/heading targets were
checked across the public pages and new supporting documents. Whitespace checks
passed. No full library regression matrix or reader retention study was run for
this documentation-only change.

The isolated published-package check installed Lifecycle 0.1.1, YIDL 0.1.2,
Astichi 1.1.3, yidl-cache 0.1.0, compat-sentinel 0.1.2 and Lark 1.3.1. Examples
therefore do not depend on unpublished sibling APIs. To rerun the standalone
examples after following the public installation instructions, from this
repository root:

```sh
ASTICHI_LOWER_ENGINE=python YIDL_LIFECYCLE_CACHE=off python - <<'PY'
from pathlib import Path
import runpy

for path in sorted(Path("examples").glob("*.py")):
    runpy.run_path(str(path), run_name="__main__")
    print("PASS", path)
PY
```

Two draft assertions were corrected during verification: ordinary constructor
arguments can be positional, and `hasattr` can see an initvar's class declaration
even though it is not a public stored value field. No runtime workaround or
implementation change was introduced.

## Authorized website deployment

The user subsequently requested deployment to GitHub Pages. That expands the
editable boundary to documentation-only MkDocs configuration, pinned site tools,
example/link validation helpers, the documentation Actions workflow and repository
Pages settings. The library implementation, SDKs and package publishing workflow
remain unchanged. The current site deploys from successful `main` documentation
builds; a new package release is not required. See
[site maintenance](documentation/README.md) for the publication contract.
