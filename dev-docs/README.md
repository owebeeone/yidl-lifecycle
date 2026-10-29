# Developer Documentation

See [release process](../RELEASE.md) and [publishing preparation](Publishing.md)
for current packaging, licensing, verified candidate checks and the ordered
publication gates. Older checkpoint statuses retain their original revisions.


## Current Surface

- [End-user documentation specification](EndUserDocumentationSpec.md): learning
  goals, research, scope and acceptance criteria for the public guide rewrite.
- [Contributor guide](ContributorGuide.md): generated builders, exact dependency
  compatibility and local development; [public user index](../docs/index.md)
  for using the library.
- [Public documentation](../docs/index.md): tutorials, task guides, field and
  transaction reference, and troubleshooting for library users.
- [Field reference](../docs/Markers.md): executable marker surface, including
  `lazy` with `mutable=True` and the `static` compatibility alias.
- [Transaction reference](../docs/TransactionReference.md): manager, assignment,
  completion and view policies. The [older API URL](../docs/ManagedContextApiDraft.md)
  remains available for existing links; proposals are labeled separately.
- [Facade ownership](../docs/FacadeOwnership.md): SVG reference graph, weak
  state caches, strong default caches, and facade collection conditions.
- [Field-kind matrix](YidlLifecycleFieldKindMatrix.md): storage and policy
  reference. Check the implementation/goldens when an older row disagrees.
- [Transaction scope ownership](TransactionScopeOwnership.md): implemented
  token-bound scope fencing and the nonpublishing ownership check.
- [Compiled code cache](LifecycleCodeCache.md): default-on consumer adapter,
  fingerprint boundary, configuration, and verification.
- [Cache startup measurements](LifecycleCodeCacheStartup.md): fresh-process
  disabled/cold/warm comparison, phase costs, and reproduction.
- [Constructor annotations](ConstructorAnnotationBinding.md): captured runtime
  binding, Python 3.14 harvesting, TDD evidence, and separate follow-up findings.
- [Repository instructions](../AGENTS.md): package ownership and coverage rules.

The library generates lifecycle behavior through its feature YIDL and the
complete generated decorator. Generic compiler work belongs in the separate
YIDL and Astichi repositories.

## Pending Work

[The shared YIDL generated code cache plan](../../yidl/dev-docs/YidlGeneratedCodeCachePlan.md)
defines standalone compiled-builder reuse. The default-on Lifecycle adapter is now
implemented, with fresh-process coverage and no YIDL core cache dependency.
Representative non-GUI startup measurements now show populated-cache savings;
automatic placement is implemented against a dual-reviewed specification;
implementation review, cross-platform approval, and publication remain pending.

[Pyrolyze's accepted L0 completion contract](../../pyrolyze/dev-docs/PytoLifecyleIntegSC3-L0Plan.md)
is the bounded manager/generated-library prerequisite. Its design and
L0-1/L0-2 library implementation are accepted; the implementation provides
completion evidence, candidate-write guards, and independently drained generated
after hooks. Private Pyrolyze consumer adoption and historical probe transition
are pending. Read that
contract and [completion behavior](TransactionScopeOwnership.md#terminal-completion-evidence)
before relying on stronger cleanup or publication evidence.

[L0 acceptance and verification](L0CompletionVerification.md) records the exact
GO/GO implementation tuple, current checks, the pre-existing Python-backend
owned-field snapshot difference, and the
closed implementation-review gate. Passing tests alone do not accept later
consumer changes or activate resource-bearing routes.

[The API proposal](ManagedContextApiProposal.md) records design direction and
unresolved options, not a second decorator API. Its review is archived; later
operator decisions implemented `lazy`/`static` and optional mutable storage.
Constructor alias proposals are not thereby implemented.

[Productionization](YidlTransactionalYidlPhaseJPlan.md) remains a future plan;
the archival move does not mark its packaging/import-policy goals complete.

## History

[History index](history/README.md) contains the completed transactional rollout,
older DDS/lifecycle experiments, parity/gap plans, and closed API review rounds.
Use those only for original rationale or exact historical evidence, not as a
current implementation checklist.

Keep current policy documents and unfinished work here. Move completed plans
and review artifacts into subject-grouped `history/` directories, preserving
verdicts and pinned revisions. Repair active links without changing historical
acceptance scope.
