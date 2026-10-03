from __future__ import annotations

from dataclasses import dataclass
import pytest

from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION
from yidl_lifecycle.transaction_yidl import TransactionManager
from yidl_lifecycle.transaction_yidl import YidlValidatorReturnedFalse


GROUP_ALPHA = "group_alpha"
GROUP_BETA = "group_beta"


@dataclass(eq=False, slots=True)
class FakeContext:
    name: str
    rank: tuple[object, ...] = ()
    validate_ok: bool = True
    require_validation: bool = False
    prepared: list[tuple[int | None, object]] | None = None
    committed: list[tuple[int, object]] | None = None
    rolled_back: list[tuple[int, object]] | None = None
    after_committed: list[tuple[int | None, object]] | None = None
    after_rolled_back: list[tuple[int | None, object]] | None = None
    validations: list[object] | None = None
    commit_error: BaseException | None = None
    rollback_error: BaseException | None = None

    def __post_init__(self) -> None:
        if self.prepared is None:
            self.prepared = []
        if self.committed is None:
            self.committed = []
        if self.rolled_back is None:
            self.rolled_back = []
        if self.after_committed is None:
            self.after_committed = []
        if self.after_rolled_back is None:
            self.after_rolled_back = []
        if self.validations is None:
            self.validations = []

    def commit_order_key_for(self, tx_key: object = DEFAULT_TRANSACTION) -> tuple[object, ...]:
        del tx_key
        return self.rank

    def requires_validation_for(self, tx_key: object = DEFAULT_TRANSACTION) -> bool:
        del tx_key
        return self.require_validation

    def validate_commit_for(self, tx_key: object = DEFAULT_TRANSACTION) -> bool:
        assert self.validations is not None
        self.validations.append(tx_key)
        return self.validate_ok

    def _prepare_commit_tx_by_key(
        self,
        tx_key: object = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        if self.commit_error is not None:
            raise self.commit_error
        assert self.prepared is not None
        self.prepared.append((tx_token, tx_key))
        return None

    def _apply_prepared_commit_tx_by_key(
        self,
        tx_key: object = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        assert self.committed is not None
        assert tx_token is not None
        self.committed.append((tx_token, tx_key))
        return None

    def _after_commit_tx_by_key(
        self,
        tx_key: object = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        assert self.after_committed is not None
        self.after_committed.append((tx_token, tx_key))
        return None

    def _rollback_tx_by_key(
        self,
        tx_key: object = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        if self.rollback_error is not None:
            raise self.rollback_error
        assert self.rolled_back is not None
        assert tx_token is not None
        self.rolled_back.append((tx_token, tx_key))
        return None

    def _after_rollback_tx_by_key(
        self,
        tx_key: object = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        assert self.after_rolled_back is not None
        self.after_rolled_back.append((tx_token, tx_key))
        return None


def test_transaction_manager_commit_and_rollback_require_balanced_begin() -> None:
    manager = TransactionManager()
    with pytest.raises(RuntimeError, match="no active yidl transaction"):
        manager.commit()
    with pytest.raises(RuntimeError, match="no active yidl transaction"):
        manager.rollback()

    manager.begin()
    manager.rollback()
    with pytest.raises(RuntimeError, match="no active yidl transaction"):
        manager.rollback()


def test_transaction_manager_enlist_commit_and_drop() -> None:
    manager = TransactionManager()
    context = FakeContext(name="ctx")

    tx = manager.begin()
    tx_id = manager.enlist(context)
    assert tx.tx_id == tx_id

    manager.drop(context, tx_id)
    assert manager.commit() == tx_id
    assert context.committed == []


def test_transaction_manager_commit_order_is_highest_rank_first() -> None:
    manager = TransactionManager()
    low = FakeContext(name="low", rank=(1,))
    high = FakeContext(name="high", rank=(2,))

    manager.begin()
    manager.enlist(low)
    manager.enlist(high)
    manager.commit()

    assert high.committed == [(1, DEFAULT_TRANSACTION)]
    assert low.committed == [(1, DEFAULT_TRANSACTION)]


def test_transaction_manager_validation_failure_rolls_back_and_resets_manager() -> None:
    manager = TransactionManager()
    context = FakeContext(name="bad", validate_ok=False, require_validation=True)

    manager.begin()
    manager.enlist(context)
    with pytest.raises(ExceptionGroup, match="yidl commit validation failed") as failure:
        manager.commit()

    assert len(failure.value.exceptions) == 1
    assert isinstance(failure.value.exceptions[0], YidlValidatorReturnedFalse)
    assert context.validations == [DEFAULT_TRANSACTION]
    assert context.rolled_back == [(1, DEFAULT_TRANSACTION)]
    assert manager.active_transaction is None
    assert manager.begin_count == 0

    tx2 = manager.begin()
    assert tx2.tx_id == 2


def test_transaction_manager_commit_failure_rolls_back_and_resets_manager() -> None:
    manager = TransactionManager()
    context = FakeContext(name="bad", commit_error=RuntimeError("commit boom"))

    manager.begin()
    manager.enlist(context)
    with pytest.raises(RuntimeError, match="commit boom"):
        manager.commit_only()

    assert context.rolled_back == [(1, DEFAULT_TRANSACTION)]
    assert manager.active_transaction is None
    assert manager.begin_count == 0

    tx2 = manager.begin()
    assert tx2.tx_id == 2


def test_transaction_manager_rollback_failure_resets_manager() -> None:
    manager = TransactionManager()
    context = FakeContext(name="bad", rollback_error=RuntimeError("rollback boom"))

    manager.begin()
    manager.enlist(context)
    with pytest.raises(RuntimeError, match="rollback boom"):
        manager.rollback()

    assert manager.active_transaction is None
    assert manager.begin_count == 0

    tx2 = manager.begin()
    assert tx2.tx_id == 2


def test_group_begin_counts_are_tracked_independently() -> None:
    manager = TransactionManager(tx_keys={GROUP_ALPHA, GROUP_BETA})
    left = FakeContext(name="left")
    right = FakeContext(name="right")

    manager.begin(GROUP_ALPHA)
    manager.begin(GROUP_ALPHA)
    manager.begin(GROUP_BETA)
    manager.enlist(left, GROUP_ALPHA)
    manager.enlist(right, GROUP_BETA)

    assert manager.commit(GROUP_ALPHA) is None
    assert left.committed == []
    assert right.committed == []

    manager.commit(GROUP_BETA)
    assert right.committed == [(1, GROUP_BETA)]

    manager.commit(GROUP_ALPHA)
    assert left.committed == [(1, GROUP_ALPHA)]


def test_multi_group_context_manager_commits_each_group() -> None:
    manager = TransactionManager(tx_keys={GROUP_ALPHA, GROUP_BETA})
    left = FakeContext(name="left")
    right = FakeContext(name="right")

    with manager.begin(GROUP_ALPHA, GROUP_BETA):
        manager.enlist(left, GROUP_ALPHA)
        manager.enlist(right, GROUP_BETA)

    assert left.committed == [(1, GROUP_ALPHA)]
    assert right.committed == [(1, GROUP_BETA)]


@pytest.mark.parametrize("keys", ((GROUP_ALPHA,), (GROUP_ALPHA, GROUP_BETA)))
def test_old_scope_cannot_commit_replacement_transactions(keys: tuple[str, ...]) -> None:
    manager = TransactionManager(tx_keys=keys)
    old_scope = manager.begin(*keys)
    manager.rollback(*keys)
    replacements = {key: manager.begin(key) for key in keys}
    context = FakeContext(name="new")
    manager.enlist(context, keys[-1])

    with pytest.raises((RuntimeError, ExceptionGroup)) as raised:
        old_scope.__exit__(None, None, None)

    errors = raised.value.exceptions if isinstance(raised.value, ExceptionGroup) else (raised.value,)
    assert len(errors) == len(keys)
    assert all("stale yidl transaction scope" in str(error) for error in errors)

    assert context.committed == []
    for key, transaction in replacements.items():
        assert manager.active_transaction_for(key) is transaction
    manager.rollback(*keys)


@pytest.mark.parametrize("keys", ((GROUP_ALPHA,), (GROUP_ALPHA, GROUP_BETA)))
def test_old_exceptional_scope_cannot_rollback_replacement_transactions(keys: tuple[str, ...]) -> None:
    manager = TransactionManager(tx_keys=keys)
    old_scope = manager.begin(*keys)
    manager.rollback(*keys)
    replacements = {key: manager.begin(key) for key in keys}
    context = FakeContext(name="new")
    manager.enlist(context, keys[-1])
    failure = ValueError("original body failure")

    assert old_scope.__exit__(ValueError, failure, None) is False

    assert context.rolled_back == []
    for key, transaction in replacements.items():
        assert manager.active_transaction_for(key) is transaction
    manager.rollback(*keys)


def test_outer_scope_after_caught_nested_failure_cannot_publish_new_transaction() -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA,))
    context = FakeContext(name="new")
    with pytest.raises(RuntimeError, match="stale yidl transaction scope"):
        with manager.begin(GROUP_ALPHA):
            try:
                with manager.begin(GROUP_ALPHA):
                    raise ValueError("nested failure")
            except ValueError:
                replacement = manager.begin(GROUP_ALPHA)
                manager.enlist(context, GROUP_ALPHA)
    assert manager.active_transaction_for(GROUP_ALPHA) is replacement
    assert context.committed == []
    manager.rollback(GROUP_ALPHA)


def test_nested_exception_preserves_original_body_failure() -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA,))
    failure = ValueError("nested failure")
    with pytest.raises(ValueError) as raised:
        with manager.begin(GROUP_ALPHA):
            with manager.begin(GROUP_ALPHA):
                raise failure
    assert raised.value is failure
    assert manager.active_transaction_for(GROUP_ALPHA) is None


def test_sole_owner_check_is_nonpublishing_and_rejects_extra_borrowers() -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA, GROUP_BETA))
    transaction = manager.begin(GROUP_ALPHA)
    other = manager.begin(GROUP_BETA)
    context = FakeContext(name="candidate")
    manager.enlist(context, GROUP_ALPHA)
    manager.require_sole_transaction_owner(transaction)
    manager.begin(GROUP_ALPHA)

    with pytest.raises(RuntimeError, match="external nested begin"):
        manager.require_sole_transaction_owner(transaction)

    assert context.validations == []
    assert context.prepared == []
    assert context.committed == []
    assert manager.commit(GROUP_ALPHA) is None
    manager.require_sole_transaction_owner(transaction)
    assert manager.active_transaction_for(GROUP_BETA) is other
    manager.rollback(GROUP_ALPHA, GROUP_BETA)


def test_sole_owner_check_rejects_missing_or_replaced_token_without_mutation() -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA,))
    transaction = manager.begin(GROUP_ALPHA)
    manager.rollback(GROUP_ALPHA)
    with pytest.raises(RuntimeError, match="missing or replaced"):
        manager.require_sole_transaction_owner(transaction)
    replacement = manager.begin(GROUP_ALPHA)
    with pytest.raises(RuntimeError, match="missing or replaced"):
        manager.require_sole_transaction_owner(transaction)
    assert manager.active_transaction_for(GROUP_ALPHA) is replacement
    manager.rollback(GROUP_ALPHA)


@pytest.mark.parametrize("completion", ("commit", "rollback"))
def test_completion_callback_cannot_partially_begin_multiple_keys(completion: str) -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA, GROUP_BETA))

    class ReentrantContext(FakeContext):
        def _after_completion(
            self, tx_key: object = DEFAULT_TRANSACTION, tx_token: int | None = None
        ) -> object:
            del tx_key, tx_token
            with pytest.raises(RuntimeError, match="completing"):
                manager.begin(GROUP_BETA, GROUP_ALPHA)
            return None

        _after_commit_tx_by_key = _after_completion
        _after_rollback_tx_by_key = _after_completion

    manager.begin(GROUP_ALPHA)
    manager.enlist(ReentrantContext(name="reentrant"), GROUP_ALPHA)
    getattr(manager, completion)(GROUP_ALPHA)

    assert manager.active_transaction_for(GROUP_ALPHA) is None
    assert manager.active_transaction_for(GROUP_BETA) is None
