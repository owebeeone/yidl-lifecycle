# Lifecycle documentation

Declare the rules for your model's fields, then use transactions to keep or
discard changes to managed values. No YIDL knowledge is needed for these guides.

## Start small

1. [Your first transaction](GettingStarted.md): install, edit, commit and cancel.
2. [Fields and live views](Concepts.md): understand what each read observes.
3. [Collections](Collections.md): edit a mutable working list safely.
4. [Coordinated transactions](Transactions.md): edit related objects together.

## Solve a task

| I want to… | Read |
| --- | --- |
| Choose which values roll back | [Field reference](Markers.md) |
| Compute defaults from other inputs | [Initialization and factories](Initialization.md) |
| Delay expensive initialization | [Lazy values](Initialization.md#lazy-values) |
| Check an edit before publishing it | [Validation and hooks](Hooks.md) |
| Keep scratch data for one transaction | [Transient values](Initialization.md#transaction-local-values) |
| Manage binding resources | [Resources and failure recovery](Resources.md) |
| Look up manager arguments and results | [Transaction reference](TransactionReference.md) |
| Explain an error or surprising value | [Troubleshooting](Troubleshooting.md) |
| Configure or clear generated-code caching | [Cache controls](Cache.md) |

## Advanced and contributor material

[Facade lifetime and ownership](FacadeOwnership.md) explains retention of live
views. [The previous transaction-guide URL](ManagedContextApiDraft.md) remains
available for existing links. [Proposals](Proposals.md) describe unavailable
options, not supported APIs.

[Contributor documentation](../dev-docs/ContributorGuide.md) covers generated
code, dependency policy and development. Historical plans, review verdicts and
experiment evidence remain under [developer documentation](../dev-docs/README.md).
