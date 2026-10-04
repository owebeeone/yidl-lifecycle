# ManagedContext API Proposal: Characterization Evidence

Date: 2026-10-03. This is document-review evidence, not new test coverage or
implementation acceptance. No runtime, tests, or golden files were changed.

Source/golden baseline: `cdf08544deea846bca4fa7e0c468ebee8d41e138`, unchanged
at draft `128a3f24a1fdce425587bb790f6d424c6307a140`.
Compatibility reference: `../pyrolyze` at
`5af937343ef3e557667d96bbf6830acce555353a`.

## Failure Characterizations

Run from this repository root. These checks execute committed generated goldens
against their fixture classes and the live transaction runtime. They do not
invoke the live generation pipeline, regenerate goldens, or claim new failure
guarantees. The equal-ranked owner precedes the failing converter by enlistment
order, so the acceptance-before-failure observation is deliberate.

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=src:tests:tests/data/gold_src:../yidl/src:../astichi/src \
../.venv/bin/python -B - <<'PY'
from functools import wraps
import runpy

from yidl_lifecycle.bindings import BindingBase
from yidl_lifecycle.lifecycle import harvest_lifecycle_definition
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager
from test_transaction_yidl import FakeContext
import yidl_transactional_phase_f_hooks as hooks
import yidl_transactional_phase_h_owned as owned

KEY = DEFAULT_TRANSACTION
hook_builder = runpy.run_path(
    'tests/data/goldens/materialized/yidl_transactional_phase_f_hooks/generated_output.py'
)['build_lifecycle_class']
owned_builder = runpy.run_path(
    'tests/data/goldens/materialized/yidl_transactional_phase_h_owned/generated_output.py'
)['build_lifecycle_class']

validation_calls = []
user = hooks._fixture_class([])
original_validator = user._validate_count
@wraps(original_validator)
def counted_validator(self):
    validation_calls.append(self.count)
    return original_validator(self)
user._validate_count = counted_validator
Counter = hook_builder(user, **dict(harvest_lifecycle_definition(user).build_kwargs))
manager = TransactionManager(tx_keys=('audit',))
counter = Counter(transaction_manager=manager)
manager.begin(KEY)
counter.count = -1
try:
    manager.commit(KEY)
except ExceptionGroup:
    pass
else:
    raise AssertionError('commit must reject the value')
assert counter.current.count == 1 and validation_calls == [-1]
manager.begin(KEY)
counter.count = -1
manager.commit_only(KEY)
assert counter.current.count == -1 and validation_calls == [-1]
print('validation: commit rejected; commit_only published without invoking validator')

manager = TransactionManager(tx_keys=('audit',))
counter = Counter(transaction_manager=manager)
manager.begin(KEY)
manager.enlist(
    FakeContext('rollback-blocker', rollback_error=RuntimeError('rollback blocked')),
    KEY,
)
working = counter.working.items
working.append(9)
try:
    manager.rollback(KEY)
except RuntimeError as exc:
    assert str(exc) == 'rollback blocked'
else:
    raise AssertionError('expected interrupted cleanup')
assert manager.active_transaction_for(KEY) is None
assert counter.working.items is working and working == [1, 2, 9]
transaction = manager.begin(KEY)
counter.working.items.append(10)
assert id(counter._y_state) not in transaction.dirty_contexts
try:
    counter.items = (3,)
except RuntimeError as exc:
    assert 'different yidl transaction' in str(exc)
else:
    raise AssertionError('expected stale-token rejection')
manager.commit(KEY)
assert counter.current.items == (1, 2)
print('cleanup: stale working list survives; new getter does not enlist; assignment rejects stale token')

owner_user = owned._fixture_class()
Owner = owned_builder(
    owner_user, **dict(harvest_lifecycle_definition(owner_user).build_kwargs)
)
freeze_user = hooks._fixture_class([])
original_key = freeze_user._commit_key
@wraps(original_key)
def equal_rank(self):
    return ()
freeze_user._commit_key = equal_rank
freeze_kwargs = dict(harvest_lifecycle_definition(freeze_user).build_kwargs)
def failing_freeze(value):
    raise ValueError('freeze failed')
freeze_kwargs['_Counter_items_freeze'] = failing_freeze
FailingCounter = hook_builder(freeze_user, **freeze_kwargs)
manager = TransactionManager(tx_keys=('audit',))
owner = Owner(transaction_manager=manager)
other = FailingCounter(transaction_manager=manager)
candidate = BindingBase()
manager.begin(KEY)
owner.child = candidate
other.working.items.append(3)
try:
    manager.commit(KEY)
except ValueError as exc:
    assert str(exc) == 'freeze failed'
else:
    raise AssertionError('expected freeze failure')
assert owner.current.child is None and candidate.is_accepted
assert other.current.items == (1, 2)
print('owned: later freeze failed; current reference unchanged; candidate acceptance persisted')

class RejectAcceptance(BindingBase):
    def accepted(self):
        raise ValueError('acceptance failed')
manager = TransactionManager()
owner = Owner(transaction_manager=manager)
first, second = BindingBase(), RejectAcceptance()
manager.begin(KEY)
owner.children = {'first': first, 'second': second}
try:
    manager.commit(KEY)
except ValueError as exc:
    assert str(exc) == 'acceptance failed'
else:
    raise AssertionError('expected partial acceptance failure')
assert owner.current.children == {} and first.is_accepted and not second.is_accepted
print('owned map: acceptance prefix persisted while current map remained unchanged')
PY
```

Observed on Python 3.12.12: exit 0.

```text
validation: commit rejected; commit_only published without invoking validator
cleanup: stale working list survives; new getter does not enlist; assignment rejects stale token
owned: later freeze failed; current reference unchanged; candidate acceptance persisted
owned map: acceptance prefix persisted while current map remained unchanged
```

## Live Walkthrough Limitation

The Surface reviewer attempted the guide's existing-API examples with
`PYTHONDONTWRITEBYTECODE=1`, the sibling source paths, and Python 3.12.12.
Decoration failed before assertions:

```text
LifecycleDefinitionError: Counter: lifecycle class build failed: 'build_lifecycle_class'
```

The lane owner's read-only probe of `_generate_lifecycle_ast` for the guide's
Counter fields produced:

```text
top-level AST: [('Pass', None)]
namespace: ['__name__']
```

This does not establish a root cause or imply that the prior I1b acceptance is
invalid. It does block claiming the guide was exercised through the live
decorator in this environment. Dependency HEADs during the probe were
`../astichi` at `387ca5e1da76204ee60922094734c13ee36383c0` and `../yidl` at
`95a6e3e52fc3d710d25c5d59315e791a3ed75cc4`; the latter has out-of-scope working
changes, so this is workspace smoke evidence, not a settled dependency release
test. Diagnose separately before continuing live-decoration-dependent work.

The successful failure characterizations above use existing generated Python
and must not be substituted for that missing end-to-end verification.
