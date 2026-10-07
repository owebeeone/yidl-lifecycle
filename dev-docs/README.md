# Developer Documentation

## Current Surface

- [Package README](../README.md): executable marker surface, including `lazy`
  with `mutable=True` and the `static` compatibility alias.
- [API guide](../docs/ManagedContextApiDraft.md): facade, assignment, and
  transaction model; proposed syntax is labeled separately.
- [Field-kind matrix](YidlLifecycleFieldKindMatrix.md): storage and policy
  reference. Check the implementation/goldens when an older row disagrees.
- [Transaction scope ownership](TransactionScopeOwnership.md): implemented
  token-bound scope fencing and the nonpublishing ownership check.
- [Repository instructions](../AGENTS.md): package ownership and coverage rules.

The library generates lifecycle behavior through its feature YIDL and the
complete generated decorator. Generic compiler work belongs in the separate
YIDL and Astichi repositories.

## Pending Work

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
