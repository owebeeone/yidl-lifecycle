# Adversarial review of Lifecycle end-user documentation

Date: 2026-10-29. Reviewed documentation commit
`efeed6ac43a991dfa6a0f1b1ad81a66150955cac` against
`be5bdce478583301ea5d5f2c85d55c73aff02b31`.

**Verdict: NO-GO for publication until findings R1–R3 are corrected and the
corrections are checked.** These require documentation/example changes, not
library or dependency changes.

## Scope and evidence

This independent adversarial review evaluates end-user correctness, usefulness,
learning progression, executable verification, and the documentation deployment
boundary. Library, SDK, publishing, and dependency implementation are
reference-only. The only authored change during review is this report. No push,
deployment, package publication, or library edit is authorized by the review.

The review read the workspace/member instructions, specification, public pages,
examples, site configuration/workflow/helpers, and relevant runtime and generated
YIDL sources. Targeted probes used the isolated installed Lifecycle 0.1.1
environment, CPython 3.14.3, `ASTICHI_LOWER_ENGINE=python`, and
`YIDL_LIFECYCLE_CACHE=off`.

Independent reruns passed all seven example scripts, fourteen guide blocks,
MkDocs strict build, and the site check (16 HTML pages, 606 local links/assets,
70 search entries). Those successes do not cover the counterexamples below.
No full platform matrix, visual browser accessibility study, or reader retention
study was performed by this review.

## Blocking findings

### R1 — P1: The hook/validation contract omits participant eligibility

Affected wording: `docs/Hooks.md:3–4` recommends validators for invariants and
completion hooks for notifications; `docs/Hooks.md:42–44` says normal completion
performs validation and `manager.validate` checks the current candidate.
`docs/TransactionReference.md:52–55` similarly describes validation without its
participant boundary. Its statement at line 110 that “ordinary application
field writes enlist automatically” also needs qualification: ordinary fields do
not enlist, and redundant managed assignment can return before enlistment.

Demonstrated behavior: sharing a manager, constructing an object, beginning a
transaction, ordinary-field changes, and an equality-elided managed assignment
do not by themselves enlist a state. Validators and completion hooks are not
global callbacks for every object sharing a manager or every successful begin.
For an initially untouched invalid state, `manager.validate` succeeds without
calling its validator. A no-op scope and an equal managed assignment invoke no
before/after hooks either.

Minimal reproduction (imports are deliberately explicit):

```python
from yidl_lifecycle.lifecycle import (
    after_commit, lifecycle, local_store, managed, validate_commit,
)
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Model:
    value: int = managed(default=-1)
    calls: list[str] = local_store(default_factory=list)

    @validate_commit()
    def valid(self):
        self.calls.append("validate")
        return self.value >= 0

    @after_commit()
    def notify(self):
        self.calls.append("after")


manager = TransactionManager()
model = Model(transaction_manager=manager)
with manager.begin(DEFAULT_TRANSACTION):
    model.value = -1
    manager.validate(DEFAULT_TRANSACTION)  # No validator is called.
assert model.calls == []
assert model.value == -1
```

Implementation evidence: `src/yidl_lifecycle/yidl/lifecycle_managed.yidl:252–262`
checks equality and returns before `_y_ensure_working_transaction`;
`lifecycle_core.yidl:458–464` enlists when working transaction storage is first
established; `src/yidl_lifecycle/transaction_yidl.py:233–244` iterates only
`validator_contexts`, and lines 767–786 add validator membership on enlistment.
Working access that actually creates a thawed managed representation, or creates
a transient overlay, can also enlist; an ordinary scalar read or scalar working
read does not do so. See `lifecycle_managed.yidl:307–330` and
`lifecycle_transient.yidl:203–249`.

Practical impact: a reader can mistakenly use `manager.validate` as a model-wide
invariant check, or expect save/notification hooks on a no-op edit. This can skip
application validation and expected notifications silently.

Minimal remedy: explain eligible/enlisted participants beside hook introduction
and validation operations. Explicitly distinguish construction validation,
ordinary-field writes, no-op assignment, and working-storage access. Tell users
to call application validation explicitly when they need to validate an unchanged
model. Add a small verified contrast for no-op versus a real managed change;
do not recommend low-level enlistment as an ordinary application workaround.

### R2 — P2: Constructor rules omit ordering and unset-lazy behavior

Affected wording: `docs/Markers.md:76–80` states that a required constructor
field has neither a default nor factory and that positional/name arguments are
accepted. `docs/Initialization.md:30` says dependencies may be declared later.
Neither explains the generated constructor's required-before-default ordering,
including inherited fields. The reference also does not explain which fields
without defaults are optional, notably lazy fields.

Demonstrated behavior:

```python
from yidl_lifecycle.lifecycle import field, lazy, lifecycle


@lifecycle
class BadOrder:
    optional: int = field(default=1)
    required: int
```

Decoration raises `LifecycleDefinitionError`, whose cause explains that a
non-default parameter would follow a default. This occurs before an instance
or a signature can be inspected. A defaulted base-class field followed by a
required subclass field has the same practical limitation.

Conversely, `value: int = lazy()` has neither default nor factory but the
constructor permits omission. `Model().value` then raises `AttributeError`
(`static field 'value' is not initialized`) until a value is assigned. A lazy
parameter also occupies a defaulted constructor position. Named factory
dependency ordering does not remove Python constructor parameter ordering.

Practical impact: straightforward model growth can fail at decoration with an
internal generator diagnostic; a reader cannot resolve it from the public
constructor/reference guidance. The required-field description also leaves
unset-lazy construction/read behavior unspecified.

Minimal remedy: document required-before-default declaration order, its
inheritance consequence, and the distinction between factory dependency order
and constructor order. Explain the `init=True` required-field case alongside
the optional lazy case, and describe unset `lazy()` reads. Add a concise
troubleshooting entry and verify the failure plus a corrected declaration.
Do not change constructor generation or dependency code.

### R3 — P2: `cls` injection is underspecified in a misleading way

Affected wording: `docs/Initialization.md:38` calls `cls` a “class provider”;
`docs/Markers.md:82–84` says it “requests the class”. In combination with the
classvar description at `docs/Markers.md:156–157`, this reasonably suggests the
generated public class and its resolved class values.

Actual `cls` injection is the original undecorated declaration class. Marker
attributes remain marker objects there. This is different from a named
classvar provider, which resolves its value:

```python
from yidl_lifecycle.lifecycle import classvar, field, lifecycle


@lifecycle
class Model:
    count: int = classvar(default=4)
    named: int = field(default_factory=lambda count: count)
    via_class: object = field(default_factory=lambda cls: cls.count)


model = Model()
assert model.named == 4
assert Model.count == 4
print(type(model.via_class).__name__)  # LifecycleMarker
```

`lambda cls: cls.count * 2` therefore fails with `TypeError` at construction;
`lambda count: count * 2` produces 8. Implementation evidence:
`src/yidl_lifecycle/lifecycle.py:74–76` passes the original `cls` into the builder,
and `src/yidl_lifecycle/yidl/lifecycle_default_factories.yidl:455–460` injects
`decorated_cls`.

Practical impact: an advertised factory provider can return marker objects or
fail when a user tries the natural classvar lookup. This is a demonstrated
limitation needing documentation, not authorization to redesign injection.

Minimal remedy: state explicitly which class `cls` means and its marker caveat;
show the named classvar-provider route. Verify the distinction in a small
example or focused documentation probe.

## Nonblocking observations and limits

- **Learning-design judgment:** the new progression is useful end-user
  documentation. The immediate edit/commit/cancel story, state table, live-view
  contrast, collections, and then coordinated edits give readers concrete
  concepts before advanced machinery. Complete examples and expected output
  are useful. Research is appropriately framed as informing editorial choices;
  the specification does not falsely claim measured retention gains. This is
  review judgment, not reader-study evidence.
- **Confirmed verification limitation:** `verify_examples.py:11–15` checks eight
  documents, excluding the field/transaction reference and Cache guide. Its
  output check at lines 35–37 uses substring matching across the whole page.
  It proves runnable examples and selected printed passages, not all reference
  assertions or exact transcript equality. Extend focused checks for R1–R3;
  do not describe existing success as complete semantic verification.
- **Resource-reference completeness opportunity:** `docs/Resources.md:14–15`
  and `docs/Markers.md:163–164` mention “supported annotated resource maps”
  without enumerating the supported annotation forms or a map example. The
  scalar example and acceptance/rollback caveats are useful and correct;
  complete map lookup guidance is a follow-up improvement, not a demonstrated
  blocker to the present scalar path. Likewise, clarify that constructing an
  owned resource reference does not itself call `accepted()` if expanding this
  section; this was confirmed in a probe.
- **Deployment configuration:** the reviewed workflow limits Pages/OIDC writes
  to the dependent deploy job, restricts deployment to the named repository's
  `main`, excludes pull-request deployment, pins Actions by commit, installs the
  package with published dependencies, and gates artifact upload on executable
  and site checks. No release/publishing implementation change is needed for
  the requested site. The configuration review does not establish successful
  hosting or verify live Pages environment settings. The parent reports that
  the pending deployment was cancelled before deployment; that operational
  result is not independently certified by this document.
- **Scope provenance:** the changes stay within the authorized documentation,
  examples, site configuration, workflow and helper boundary. No SDK/library
  change is needed to address any review finding. Existing design/evidence
  remains accessible, and the spec distinguishes the subsequent Pages
  authorization from the earlier content-only scope.

## Reassessment gate

Correct R1–R3 in public guidance/reference, add narrowly targeted executable
evidence, rerun examples and strict site checks, and obtain a review of those
corrections before another publication attempt. Preserve this initial verdict
and append a reassessment with its reviewed revision and evidence. A passing
build alone does not supersede this NO-GO.

## Reassessment of remediation — 2026-10-29

**Verdict: GO for publication of the reviewed documentation state below.**
R1–R3 are resolved. This supersedes the initial publication hold for this
specific state; the original findings and NO-GO remain above as review history.
There are no remaining blocking findings from this review. This is approval of
documentation correctness and its publication gate, not certification of new
library behavior or of a live deployment.

The reassessment independently inspected the complete diff of the seven
remediation files against `efeed6ac43a991dfa6a0f1b1ad81a66150955cac`.
The user confirmed that participant eligibility is expected behavior; the
remediation correctly documents it instead of changing runtime behavior.

- **R1 closed:** `docs/Hooks.md:7–18` explicitly distinguishes enlisted states,
  construction, ordinary-field edits, equality-elided assignments, working
  materialization, and application validation of unchanged data.
  `docs/TransactionReference.md:52–58`, `71–75`, and `119–122` qualify validation
  and automatic enlistment. The updated `examples/validation.py` demonstrates
  construction/no-op/plain-field/equal-assignment/scalar-working-read cases
  skipping callbacks, followed by a real managed replacement running
  validation, before, and after hooks. A separate reviewer probe confirmed
  that obtaining a thawed working list enlists the object even without a
  content change and invokes the three callbacks at commit.
- **R2 closed:** `docs/Markers.md:81–88` and
  `docs/Initialization.md:65–71` explain required-before-default constructor
  ordering, inheritance, and that even bare `lazy()` counts as a defaulted
  constructor parameter. The lazy section and troubleshooting explain the
  unset read failure and first assignment. The updated initialization example
  verifies failed default-before-required ordering, corrected required-first
  ordering, inherited-default failure, and unset-lazy read/first assignment.
- **R3 closed:** `docs/Initialization.md:38–56` and
  `docs/Markers.md:90–93` distinguish the original undecorated `cls` and marker
  attributes from resolved named classvar providers. The runnable guide example
  obtains 8 from named `SCALE` and a class name from `cls.__name__`; the separate
  initialization example additionally verifies that `cls.SCALE` is a
  `LifecycleMarker` while the public generated class exposes 4.

The reviewer independently reran all seven examples and fifteen guide blocks
against installed Lifecycle 0.1.1, YIDL 0.1.2, Astichi 1.1.3, yidl-cache 0.1.0,
compat-sentinel 0.1.2 and Lark 1.3.1 on CPython 3.14.3, with the Python backend
and persistence disabled. All passed. The strict MkDocs build and site checker
passed with 16 HTML pages, 608 local links/assets and 70 search entries.
Whitespace checks passed. The parent's separate Python 3.12 verification is
additional evidence; this reassessment does not present it as an independent
reviewer run. The remaining nonblocking observations above are unchanged.

The following SHA-256 digests identify the reviewed remediation state relative
to the original reviewed commit. The report itself is excluded because this
append changes it. No source implementation, package publishing workflow, SDK,
or dependency change forms part of this acceptance.

| File | SHA-256 |
| --- | --- |
| `docs/Hooks.md` | `5ebc78d8ed0d402e025f9f945f15b410ab6e70201e85ce818dd25f4edb632e59` |
| `docs/Initialization.md` | `d44fb61ca07693227fe6e513b5af2bff746724d1cbd11e61a9aeb6dd1ef55ab1` |
| `docs/Markers.md` | `49d9160cdce9c772d5403a6b3b8b6930bb598526f70fa0954df0771b18712110` |
| `docs/TransactionReference.md` | `c847dd682b0ed1623a7c731324d774707344a923a737bd5298335bfe72f4a946` |
| `docs/Troubleshooting.md` | `b75b99ecf39878212947351f98742e85a358d2eb57a31514f05e92ec78d760d6` |
| `examples/validation.py` | `02f6ebde1dc6694191498bee8ab948517a54bf2e3ceb173f24b9a48382db18f7` |
| `examples/initialization.py` | `778da3829d7aea1e6a17056886a6dc68d85eed6adfe19623f82732334037cd63` |

No push or deployment was performed by this reviewer. Publication and subsequent
live-site verification remain actions for the parent task within the user's
existing authorization.

## Addendum: callback argument summary — 2026-10-29

**Verdict: GO for the two-file documentation update identified below.** No
blocking findings remain. This addendum preserves the prior review verdicts;
it reviews the small callback table/reference change against
`746f36a0f39a79c8ea47528f544b8c1e66fbbc7f`, not a new library implementation.
Only this report was edited by the reviewer. No push or deployment was performed.

The reviewed boundary is `docs/Initialization.md` and `docs/Markers.md`: one
callback argument/timing table, its reference link, and correction of the
overbroad statement about named transient working-factory providers. The
transient correction is justified by existing implementation behavior and stays
within the documentation task. Library, SDK and dependency implementation remain
reference-only.

The table correctly distinguishes keyword factory-provider injection from
positional conversions and bound zero-argument hook methods. Construction and
lazy factories preserve the documented original-class `cls` behavior and the
marker's self opt-in restriction. The transient row now explicitly maps `self`
to the default facade, `current` to the committed view, and `working` to the
working view. It also states that default-view reads can trigger the working
factory, and that earlier assignment bypasses it. This avoids implying that
injected `self` is whichever facade initiated access.

The final table also explicitly distinguishes construction `self` (the
constructing default facade) from lazy-factory `self` (the facade performing
the first read). A focused installed-package identity probe confirmed both:
construction captured the model's default facade, while a first lazy read
through `.current` supplied and cached that current facade. Subsequent default
access returned the same cached result. The opt-in restriction remains stated
for construction/lazy factories.

The existing source at `src/yidl_lifecycle/yidl/lifecycle_transient.yidl`
(`BuildTransientFactsBody` and the `TransientWorkingFactory*Arg` resources)
confirms that direct named working-factory providers must be retained initvars;
ordinary field/classvar providers are rejected. `self`, `current`, and `working`
are special injections without the construction-factory self opt-in, while
`cls` has no special injection. Views provide the supported route to ordinary
field/classvar values. The adjacent guide/reference correction accurately
states these restrictions.

A focused reviewer probe against installed Lifecycle 0.1.1 confirmed:

- A retained initvar and all three views are supplied without a self opt-in.
  With pending scalar value 4 and committed value 2, a working factory received
  the original initvar 7 and observed default/current/working values 4/2/4.
- Even when invoked through `model.working.scratch`, injected `self` is
  `model.default`; the other injected facades have their respective identities.
- Direct ordinary-field and classvar working-factory parameters fail decoration
  with the non-initvar-provider diagnostic. An undeclared `cls` parameter fails
  with the unknown-provider diagnostic.

The reviewer also independently reran all seven examples and fifteen executable
guide blocks on CPython 3.14.3 with the installed published dependency tuple
recorded in the reassessment above, Python backend, and persistence disabled.
All passed. Strict MkDocs build and site checking passed with 16 HTML pages,
615 local links/assets, and 71 search entries. Whitespace checks passed. These
mechanical checks supplement the source/probe review; the prose table itself
is not automatically executed by the guide-block checker.

| Reviewed file | SHA-256 |
| --- | --- |
| `docs/Initialization.md` | `7e5d8ce3b1bc33805a4e59fc94bf5e24e62b6df65095ccf5c8e62f2cb8de5b7f` |
| `docs/Markers.md` | `e5a1954752ad5f6061517dea5e73cc6161f857ecaa8df0c40ce71a66de63e1d1` |
