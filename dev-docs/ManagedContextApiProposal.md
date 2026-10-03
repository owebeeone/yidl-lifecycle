# ManagedContext API Proposal

## Status And Review Scope

Status: DRAFT for design review, 2026-10-03. This is not an implementation
checkpoint or operator approval of the proposed API changes.

The user requested a reviewable proposal before further LCM migration work.
The primary mental model is **transaction-scoped editing of managed state**,
not switching an entire Python object between frozen and mutable classes.

Pyrolyze's LCM adapter locally aliases `yidl_lifecycle.lifecycle.lifecycle` as
`managed_context`. The separate legacy `pyrolyze.lifecycle.managed_context`
still exists and does not accept the same marker objects. Only the LCM alias
is equivalent to the library decorator. This proposal introduces no second
YIDL decorator, no `ManagedContext` base class, and no decorator rename.

Review the document and `docs/ManagedContextApiDraft.md` together. The latter
is a user-facing draft, with proposed-only syntax labeled separately from
the existing executable surface.

Review tier: dual peer-blind Consistency/Safety, plus a cold-read Surface
review of the user-facing draft. Acceptance means a technically coherent
proposal, not implemented behavior, a release freeze, or permission to resume
the integration with changed transaction boundaries.

## Controlling Material

- `AGENTS.md`: package ownership and canonical success coverage.
- `dev-docs/YidlTransactionalYidlPhaseF-1Plan.md`: working/staged/current
  storage and transaction completion intent.
- `dev-docs/YidlPyroCloseTheGapPlan.md`: retained inputs, trusted self
  factories, and non-transactional storage.
- `dev-docs/YidlLifecycleFieldKindMatrix.md`: field-policy vocabulary; known
  conflicts are called out below rather than treated as implemented behavior.
- `../pyrolyze/dev-docs/PytoLifecyleIntegPlan.md`: preserve existing completion
  owners and publication boundaries during holder replacement. Stronger
  outer atomicity, comprehensive containment, and lifetime redesign remain
  separate decisions.

Source baseline before this draft:

| Repository | Revision | Role |
| --- | --- | --- |
| `yidl-lifecycle` | `cdf08544deea846bca4fa7e0c468ebee8d41e138` | Markers, harvester, templates, transaction implementation and goldens |
| `../pyrolyze` | `5af937343ef3e557667d96bbf6830acce555353a` | Accepted I1b construction/attachment checkpoint and integration constraints |

The review prompts pin the committed draft revision separately. Parent
workspace changes and unrelated dependency work are outside this object.

## Decisions Proposed

| ID | Proposal | Classification |
| --- | --- | --- |
| A1 | Present managed fields as editable only within their active transaction key | Contract clarification |
| A2 | Document facades as live access policies, not whole-object freezing or snapshots | Contract clarification |
| A3 | State the limits of rollback, reference immutability, and freeze/thaw | Contract clarification |
| A4 | Add an optional constructor spelling, `init_name`, without creating a second field or dependency name | Additive API change requiring implementation approval |
| A5 | Discuss what non-write-once `static` would mean before choosing its policy | Open operator decision; retain current behavior meanwhile |
| A6 | Keep value initialization separate from graph attachment and completion ownership | Preserve accepted integration boundary |
| A7 | Preserve convenient marker names while treating their policies as independently composable YIDL facts | Design constraint; no generic policy-builder API |

## A1: Transaction-Scoped Editing

For `managed` and the transactional reference stored by `owned`:

1. Assignment through default or working requires an active transaction for
   that field's `tx_key`, including assignments later elided by comparison.
2. Assignment records a pending replacement; it does not overwrite committed
   current state immediately.
3. Outermost ordinary `commit` and successful outermost scope exit validate,
   prepare converted values, and apply prepared values. In healthy completion,
   aborting clears pending/staged values at that boundary; the failure limits
   below qualify that statement.
4. After completion, further assignment again requires an active transaction.

This describes assignment through generated accessors. It does not intercept
arbitrary mutations to objects returned by an accessor. `owned` manages the
stored resource reference; it does not make the resource's internals
transactional or give the parent exclusive ownership of that resource.

No implicit transaction is started by an assignment. Default-facade syntax
remains supported; explicit `.working` syntax is useful when the code must
make the pending view visible, especially for thawed editable aggregates.

### Completion Ownership And Scope

The manager owns completion. Object `begin`, `validate`, `commit_only`,
`commit`, and `rollback` methods remain conveniences delegating to that manager,
not participant-selective operations. A shared manager/key can complete other
enlisted objects. Passing a manager does not transfer completion ownership to
every object using it.

`commit_only` deliberately bypasses validators and can publish values a
validator would reject. Its completion owner must assume validation
responsibility; it is not the ordinary application completion API. A prior
`validate` does not certify subsequent edits. Prefer `commit` or an ordinary
manager scope for normal completion. Nested completion that only reduces depth
does not validate or publish yet.

Use an explicit key in examples. Today, omitting keys on manager or object
operations selects the default key **and all configured non-default keys**.
This proposal does not change that default. Multiple keys complete separately,
not as one atomic transaction across keys.

Nested begins on the same key join its active transaction and increase depth;
they are not savepoints. A nested rollback aborts the joined key transaction,
not just that nested body's edits. Do not promise isolated child recovery from
this mechanism.

### Failure Contract: Intent Versus Implementation

The Phase F-1 design intends preparation failure to prevent publication and
completion callbacks to drain/report failures appropriately. At the pinned
source baseline, participant apply, rollback, and after-hook loops can stop
at the first exception. Some participants can consequently remain uncleared
or unprocessed, even though manager bookkeeping is reset.

That contaminated state can still expose its stale working overlay through
default/working getters after the manager becomes inactive. Starting another
transaction is not recovery: a getter can return that overlay without enlisting
it, while assignment rejects its old token. Discarding previously returned
references alone does not fix the participant. Require verified cleanup or
supported domain recovery before reusing that state cohort; otherwise stop
using and reconstruct it as appropriate to the application's ownership rules.
No general public guaranteed-recovery operation is introduced here.

This proposal does not assert that those gaps are fixed, that every exception
undoes committed values, or that a successful child publication is provisional
until its parent completes. The existing integration plan's L0/D4 gate owns
that correction. It must be approved and verified before relying on stronger
multi-participant failure guarantees. An after-commit failure is not permission
to roll back already published values.

No concurrent thread/task editing isolation is provided by this proposal.
Facades and the manager do not supply locks, MVCC, or task-local working slots.
The documented model assumes serialized access to a manager/state cohort.

## A2: Facades Are Live Access Policies

The following access behavior assumes successfully initialized, healthy state
whose previous completion did not leave stale working values/tokens. The
failure section above governs contaminated state; an inactive manager alone
does not establish that these healthy-state preconditions hold.

| Field category | Default facade | Current facade | Working facade |
| --- | --- | --- | --- |
| `managed` / `owned` reference | Pending replacement if present, otherwise committed; transaction-gated assignment | Committed value; assignment rejected | Pending replacement with committed fallback; transaction-gated assignment |
| Managed field with thaw | Default overlay reads do not initiate thaw | Committed representation | In an active key, first editable access enlists and thaws; outside it, returns committed representation |
| `field`, `binding`, `local_store` | Shared non-transactional storage | Same storage and assignment policy | Same storage and assignment policy |
| `const` | Readable; replacement rejected | Same | Same |
| `static` | Shared lazy storage; currently write-once, replacement policy unresolved under A5 | Same | Same |
| `transient` | Active-key access initializes/enlists transaction-local storage; inactive access returns its construction baseline | Construction baseline, never the transaction-local value | Same active/inactive behavior as default |
| `initvar` | No public accessor; may be retained internally for later consumers | Same | Same |
| `classvar` | Common class attribute | Same | Same |

`current` is a live committed view. A previously acquired facade sees later
commits. It is not a historical snapshot. User methods invoked on a facade
resolve lifecycle properties through that facade; they can still have external
side effects and can write non-transactional fields.

The default facade is the ordinary object identity. Do not remove it, force
all scalar assignments through `.working`, add a fourth facade, or rename
`current`/`working`/`default` in this proposal.

The model retains existing state/facade reference ownership: facades strongly
reference state; state weakly caches facades; the default facade retains the
created secondary facades. This proposal does not create strong reverse links
from state to default or retained inputs to their consuming facades.

## A3: Reference And Aggregate Mutability

`const` means the stored reference cannot be replaced through generated
accessors after initialization. For example, a list referenced by a const field
can still be mutated. Do not advertise recursively immutable Python objects.

Similarly, mutable values in plain fields, bindings, classvars, or scratch
storage are outside transaction rollback. Sharing one manager does not change
their field policies.

For transactionally edited aggregates, `freeze`/`thaw` must provide sufficient
separation between committed and working representations. The normal pattern
is an immutable committed value and a detached mutable working value:

```python
items: tuple[int, ...] = managed(default=(), thaw=list, freeze=tuple)
```

Inside its active transaction, `obj.working.items.append(1)` uses a working
copy. Commit prepares the tuple; rollback discards the working reference.
This shallow tuple/list conversion only isolates elements that themselves do
not expose shared mutable state. Deeper structures require appropriate
conversion functions; annotations do not certify separation.

Mutable working references must not be reused across transaction boundaries.
Discarding a working slot does not revoke an already returned Python list.
This proposal adds no revocable proxy or reference-tracking runtime.

### Owned Acceptance Is A Separate Effect

In the pinned implementation, transactional owned candidates receive
`BindingBase.accepted()` during preparation, before reference publication.
A later conversion/prepare failure can leave the current reference unchanged
while a caller-held candidate remains accepted. Owned-map preparation can
accept a prefix before a later item fails; reference rollback does not undo
those acceptance effects.

Consequently, preparation failure prevents the corresponding current-slot
replacement, not all external/resource effects. Do not equate successful
reference publication with the first acceptance event, assume a failed
candidate was never accepted, or add lifetime/acceptance-timing redesign under
this documentation proposal. That behavior needs a separately approved resource
contract if consumers require stronger guarantees.

Conversion failure during preparation is distinct from an exception after
publication. Tests must keep those cases separate; the latter cannot promise
undo. Do not replace the staged prepare/apply protocol with eager conversion
in every setter or transaction-manager calls on every ordinary getter.

## A4: Constructor Names Without Copying Factories

The current LCM code repeatedly declares an initvar and a trivial copying
factory solely to accept a public constructor name while exposing a private
stored property. A proposed optional marker argument is:

```python
_parent_state_mgr: object = field(init_name="parent_state_mgr", default=None)
_slot_id: object = const(init_name="slot_id", default=None)
```

This is **proposed syntax**, not accepted by current markers. Keep `initvar`
for genuine constructor-only providers, retained inputs, and computed values.

### Exact Naming Rules

- Add keyword-only `init_name: str | None = None` to init-bearing markers:
  `field`, `const`, `static`, `managed`, `owned`, `binding`, `transient`, and
  `initvar`. `classvar` and `local_store` do not gain constructor parameters.
- For a new field, omission uses its declared field name. On an override,
  omission inherits the existing effective constructor name. An explicit
  value on an override may repeat that name but may not rename it in this
  first implementation; reject renaming at decoration time.
- A non-`None` `init_name` with `init=False` is rejected. The name must be a non-keyword
  Python identifier, must not use generated reserved prefixes, and must not
  collide with another effective constructor name, `self`, or
  `transaction_manager`. Validate all constructor-participating fields against
  the entire resolved local/inherited field set; `init=False` fields do not
  reserve constructor names.
- Field identity, property names, slots, ordering, and dependency-provider names
  remain based on the declared field name. The constructor alias is not a
  second factory provider, public property, or retained initvar.
- The generated function accepts the alias only. Defaults, requiredness,
  positional/keyword behavior, and factory override behavior otherwise remain
  as they were. No generic `**kwargs` dispatcher is introduced.
- Alias values used by construction factories are lowered to the same declared
  provider/local names before their consumers run. In particular, an aliased
  initvar still supplies its declared initvar name to factories and retained
  storage. The Python parameter spelling is not allowed to leak into dependency
  identity or to cause an undefined generated local.
- Diagnostics identify the declared field and, when relevant, the constructor
  alias. Named dependencies resolve declared field names, not aliases. A
  consumer of a removed initvar must be migrated explicitly; alias sugar is
  not permission to silently retarget its dependency.

Generated construction should be equivalent to:

```python
def __init__(self, parent_state_mgr=None, slot_id=None, *, transaction_manager=None):
    # Existing generated state and manager initialization precedes these writes.
    state._y__parent_state_mgr_value = parent_state_mgr
    state._y__slot_id_value = slot_id
```

This is an outline, not a complete executable constructor. Store constructor
name separately from `FieldName` in lifecycle facts and metadata. Legacy v1
metadata without that optional name resolves it to the field name. Keep the
generated private build boundary unpacked; this feature does not restore
default/default_factory dictionaries there.

Add the lifecycle-specific fact/property in its owning schema. No generic YIDL
grammar change is authorized. If implementing it requires a new compiler
surface, stop and propose that separately.

## A5: Resolve The Static Conflict Explicitly

Evidence of the conflict:

- `dev-docs/YidlLifecycleFieldKindMatrix.md` says static is non-transactional,
  lazy, and rewritable.
- `dev-docs/YidlPyrolyzeLifecycleParityPlan.md` describes lazy/write-once static.
- `lifecycle_markers.static` says write-once; the three static property
  templates reject a second assignment.
- `tests/data/gold_src/yidl_transactional_parity_fields1.py` asserts that
  rejection. Existing passing goldens do not resolve which policy is desired.
- `../pyrolyze/src/pyrolyze/lifecycle.py` also currently rejects a second static
  assignment. Rewritable static would intentionally differ from that legacy
  behavior; this is not a claim of existing Pyrolyze parity.

The user explicitly requested further discussion of non-write-once static.
Do not select rewritable behavior merely because one document says so. Current
code and rejection goldens remain unchanged until that discussion settles a
policy. The options below are discussion alternatives, not new API options:

1. **Lazy, write-once storage:** the implemented policy. The first explicit
   value or successful lazy initialization settles the value; replacement
   raises. It differs from const by allowing initialization on first use or
   first assignment rather than requiring construction-time initialization.
2. **Lazy ordinary storage:** a possible non-write-once meaning. First read
   initializes an unset value. Later assignments replace the shared value
   immediately, without transaction participation or automatic recomputation.
   A subsequent read returns the replacement, not a new factory result.
3. **Invalidatable computed cache:** a different facility. Reset/invalidation
   would permit a future factory evaluation. Neither "static" nor permitting
   assignment specifies when that should happen or which dependencies trigger
   it. No such reset/invalidation surface is proposed here.

Before selecting option 2, decide whether lazy initialization itself adds useful
meaning beyond an ordinary field; whether replacement is allowed through every
facade; and whether the value is strictly per-instance despite the name static.
If reset or automatic invalidation is wanted, discuss its lifecycle separately
instead of silently attaching it to assignment permission.

No new `write_once` switch, field kind, reset method, or lazy const behavior is
authorized by this review. Once the operator settles A5, reconcile the marker
docstring, templates when necessary, matrix, affected parity-plan clauses, and
canonical evidence. Any permission change is a compatibility change, not merely
documentation repair. Preserve historical reports and name superseded clauses.

## A6: Initialization And Domain Effects

Factory parameter names describe inputs read at the factory's evaluation
point. They do not declare continuously maintained formulas. Construction,
lazy static initialization, and per-transaction transient initialization remain
different lifetimes. Caller-supplied values suppress init-parameter factories;
`init=False` construction factories run at their generated evaluation step.
Trusted `allow_self_factory` remains explicit; no new implicit self injection
or `__init__`/`__post_init__` chaining is introduced.

Value factories should produce values. Attachment, registration, publication,
and external resource effects retain explicit domain boundaries. In particular,
Pyrolyze's I1b `create` path completes construction before graph attachment.
An alias can eliminate a copying factory; it must not move attachment back
into another default factory or make raw constructors attach implicitly.

Keep existing manager/key cohorts while replacing holders. Neither A1 nor
the user-facing examples authorize one shared graph manager, root-wide
atomicity, changed child acceptance timing, or stronger failure containment.

## A7: Policy Composition Without A Configuration Bag

Keep the existing author-facing helpers. They are readable bundles of policies:
storage, initialization timing, assignment authority, transaction key,
conversion, comparison, and resource constraints.

Compose those policies using existing facts, matchers, resources, productions,
and phases. Do not create a handwritten parallel policy engine, a new kind
lattice, or a public generic builder accepting arbitrary policy combinations.
No broad YIDL refactor is a prerequisite for this proposal. The rule constrains
future implementation, rather than asking for speculative abstractions now.

## Implementation And Evidence Sequence After Approval

This is a bounded follow-up sequence, not an automatically authorized roll-build.

1. **Contract documentation.** Reconcile the user guide and field matrix with
   actual implemented facade/default-key behavior. Identify historical versus
   current claims, including parameterized `local_store` support. Link the
   existing L0 failure gate; do not self-close it from documentation.
2. **Constructor alias mechanics.** Add marker/harvester metadata and naming
   validation, then constructor resource bindings. Preserve inherited aliases
   and unchanged field dependency identity; regenerate the decorator artifact.
3. **Constructor alias golden.** Extend a canonical fixture with aliased plain,
   const, managed and initvar values, an inherited override, and parameterized
   factories. Compare complete decorator and generated output source, execute
   both, and inspect the actual constructor signature. Verify aliases are not
   additional properties/providers. Test the unchanged spelling alongside it.
4. **Static decision, after discussion.** If retaining write-once, reconcile
   the contradictory matrix without changing runtime or rejection goldens. If
   choosing lazy ordinary storage, approve the exact replacement permissions
   first, then update the existing canonical const/static fixture to show
   explicit-first-write, factory-first-read, subsequent replacement on each
   permitted facade, constructor override, and persistence through an abort.
   Keep const rejection coverage. Reset/invalidation is not part of either path.
5. **LCM use, separately.** Replace only proven identity-copy declaration pairs.
   Preserve genuine initvar consumers, manager injection, concrete constructor
   failure isolation, raw-constructor detachment, and attachment order. Re-run
   the accepted I1b canonical fixture and focused integration gates.

The document-review characterization commands and their limits are recorded in
`dev-docs/ManagedContextApiProposal-Checks.md`. They exercise committed generated
goldens, not a regenerated decorator, and do not close the L0/D4 implementation
gate or certify that the live generation pipeline passes its smoke test.

Use narrow tests for alias recognition, invalid names, resolved-name collisions,
unsupported options, inheritance renaming, and missing dependency diagnostics.
Successful end-to-end behavior belongs in canonical goldens, not duplicated
bespoke tests. Performance checks must confirm alias lowering generates direct
assignments with no runtime alias map/lookup.

## Review Questions And Operator Decisions

1. Is transaction-scoped editing the right primary explanation while preserving
   explicit non-transactional fields and the implemented failure limitations?
2. Is `init_name` worth adding, with the constructor-only namespace above?
3. What should non-write-once static mean, and is that preferable to the current
   lazy/write-once policy? Discussion must settle this before any change.
4. Are any of these changes necessary before I3a, as opposed to a separately
   approved lifecycle-library change? This proposal does not answer by silently
   expanding the Pyrolyze migration gates.

Technical review acceptance does not select these operator choices. No runtime
code, goldens, existing acceptance reports, dependency pointers, or transaction
boundaries are changed by this document-review pass.
