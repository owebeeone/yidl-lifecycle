from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from dataclasses import dataclass
from dataclasses import field
import pytest

from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION
from yidl_lifecycle.transaction_yidl import LifecycleTransaction
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

    def commit_order_key_for(
        self, tx_key: object = DEFAULT_TRANSACTION
    ) -> tuple[object, ...]:
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
    with pytest.raises(
        ExceptionGroup, match="yidl commit validation failed"
    ) as failure:
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
def test_old_scope_cannot_commit_replacement_transactions(
    keys: tuple[str, ...],
) -> None:
    manager = TransactionManager(tx_keys=keys)
    old_scope = manager.begin(*keys)
    manager.rollback(*keys)
    replacements = {key: manager.begin(key) for key in keys}
    context = FakeContext(name="new")
    manager.enlist(context, keys[-1])

    with pytest.raises((RuntimeError, ExceptionGroup)) as raised:
        old_scope.__exit__(None, None, None)

    errors = (
        raised.value.exceptions
        if isinstance(raised.value, ExceptionGroup)
        else (raised.value,)
    )
    assert len(errors) == len(keys)
    assert all("stale yidl transaction scope" in str(error) for error in errors)

    assert context.committed == []
    for key, transaction in replacements.items():
        assert manager.active_transaction_for(key) is transaction
    manager.rollback(*keys)


@pytest.mark.parametrize("keys", ((GROUP_ALPHA,), (GROUP_ALPHA, GROUP_BETA)))
def test_old_exceptional_scope_cannot_rollback_replacement_transactions(
    keys: tuple[str, ...],
) -> None:
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


def test_outer_scope_after_caught_nested_failure_cannot_publish_new_transaction() -> (
    None
):
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
def test_completion_callback_cannot_partially_begin_multiple_keys(
    completion: str,
) -> None:
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


@dataclass(eq=False, slots=True)
class CompletionContext(FakeContext):
    events: list[str] = field(default_factory=list)
    errors: dict[str, BaseException] = field(default_factory=dict)
    actions: dict[str, Callable[[], object]] = field(default_factory=dict)

    def _step(self, phase: str) -> None:
        self.events.append(f"{phase}:{self.name}")
        action = self.actions.get(phase)
        if action is not None:
            action()
        error = self.errors.get(phase)
        if error is not None:
            raise error

    def commit_order_key_for(
        self, tx_key: object = DEFAULT_TRANSACTION
    ) -> tuple[object, ...]:
        self._step("order")
        return self.rank

    def validate_commit_for(self, tx_key: object = DEFAULT_TRANSACTION) -> bool:
        self._step("validate")
        return self.validate_ok

    def _prepare_commit_tx_by_key(self, tx_key: object, tx_token: int | None) -> None:
        self._step("prepare")

    def _apply_prepared_commit_tx_by_key(
        self, tx_key: object, tx_token: int | None
    ) -> None:
        self._step("apply")

    def _rollback_tx_by_key(self, tx_key: object, tx_token: int | None) -> None:
        self._step("discard")

    def _after_commit_tx_by_key(self, tx_key: object, tx_token: int | None) -> None:
        self._step("after_commit")

    def _after_rollback_tx_by_key(self, tx_key: object, tx_token: int | None) -> None:
        self._step("after_rollback")


@pytest.mark.parametrize(
    ("phase", "method", "expected", "publication", "discard", "after"),
    (
        (
            "prepare",
            "commit_only",
            [
                "order:A",
                "order:B",
                "prepare:A",
                "discard:A",
                "discard:B",
                "after_rollback:A",
                "after_rollback:B",
            ],
            False,
            True,
            True,
        ),
        (
            "apply",
            "commit_only",
            [
                "order:A",
                "order:B",
                "prepare:A",
                "prepare:B",
                "apply:A",
                "apply:B",
                "discard:A",
                "after_rollback:A",
                "after_commit:B",
            ],
            False,
            True,
            True,
        ),
        (
            "after_commit",
            "commit_only",
            [
                "order:A",
                "order:B",
                "prepare:A",
                "prepare:B",
                "apply:A",
                "apply:B",
                "after_commit:A",
                "after_commit:B",
            ],
            True,
            False,
            False,
        ),
        (
            "discard",
            "rollback",
            ["discard:A", "discard:B", "after_rollback:B"],
            False,
            False,
            True,
        ),
        (
            "after_rollback",
            "rollback",
            ["discard:A", "discard:B", "after_rollback:A", "after_rollback:B"],
            False,
            True,
            False,
        ),
        (
            "order",
            "commit_only",
            [
                "order:A",
                "discard:A",
                "discard:B",
                "after_rollback:A",
                "after_rollback:B",
            ],
            False,
            True,
            True,
        ),
    ),
)
def test_completion_failure_drains_only_eligible_phases(
    phase: str,
    method: str,
    expected: list[str],
    publication: bool,
    discard: bool,
    after: bool,
) -> None:
    manager = TransactionManager()
    events: list[str] = []
    failure = ValueError(f"{phase} failed")
    first = CompletionContext(name="A", events=events, errors={phase: failure})
    second = CompletionContext(name="B", events=events)
    transaction = manager.begin()
    manager.enlist(first)
    manager.enlist(second)

    with pytest.raises(ValueError) as raised:
        getattr(manager, method)()

    assert raised.value is failure
    assert events == expected
    outcome = transaction.completion
    assert outcome is not None
    assert outcome.publication_started is (phase in {"apply", "after_commit"})
    assert outcome.publication_complete is publication
    assert outcome.discard_complete is discard
    assert outcome.after_actions_complete is after
    assert outcome.ownership_preserved and outcome.finalized
    assert outcome.failures == (failure,)
    assert manager.active_transaction is None and manager.begin_count == 0
    assert any(f"phase={phase}" in note for note in failure.__notes__)


def test_prepare_and_cleanup_errors_preserve_original_occurrence_order() -> None:
    manager = TransactionManager()
    events: list[str] = []
    prepare = ValueError("prepare failed")
    discard = RuntimeError("discard failed")
    after = LookupError("after failed")
    first = CompletionContext(
        name="A", events=events, errors={"prepare": prepare, "discard": discard}
    )
    second = CompletionContext(
        name="B",
        events=events,
        errors={
            "prepare": AssertionError("must not prepare B"),
            "after_rollback": after,
        },
    )
    transaction = manager.begin()
    manager.enlist(first)
    manager.enlist(second)

    with pytest.raises(ExceptionGroup) as raised:
        manager.commit_only()

    assert raised.value.exceptions == (prepare, discard, after)
    assert transaction.completion.failures == (prepare, discard, after)
    assert not transaction.completion.publication_started
    assert not transaction.completion.discard_complete
    assert not transaction.completion.after_actions_complete
    assert events[-3:] == ["discard:A", "discard:B", "after_rollback:B"]


def test_apply_failure_can_mutate_current_and_is_not_reported_as_undone() -> None:
    manager = TransactionManager()
    values = {"current": 0, "pending": 1}
    failure = ValueError("mutated then failed")
    context = CompletionContext(
        name="partial",
        errors={"apply": failure},
        actions={
            "apply": lambda: values.update(current=1),
            "discard": lambda: values.update(pending=0),
        },
    )
    transaction = manager.begin()
    manager.enlist(context)
    with pytest.raises(ValueError):
        manager.commit_only()
    assert values == {"current": 1, "pending": 0}
    assert transaction.completion.publication_started
    assert not transaction.completion.publication_complete
    assert transaction.completion.discard_complete


@pytest.mark.parametrize("method", ("commit_only", "rollback"))
def test_empty_completion_records_entered_phases_and_survives_stale_scope(
    method: str,
) -> None:
    manager = TransactionManager()
    transaction = manager.begin()
    assert transaction.completion is None
    manager.begin()
    assert manager.commit() is None
    assert transaction.completion is None
    assert getattr(manager, method)() == transaction.tx_id
    outcome = transaction.completion
    assert outcome is not None
    assert not outcome.publication_started
    assert outcome.publication_complete is (method == "commit_only")
    assert outcome.discard_complete is (method == "rollback")
    assert (
        outcome.after_actions_complete
        and outcome.finalized
        and outcome.ownership_preserved
    )
    assert outcome.tx_key == transaction.tx_key and outcome.tx_id == transaction.tx_id
    assert outcome.failures == ()
    with pytest.raises(FrozenInstanceError):
        outcome.finalized = False
    with pytest.raises(AttributeError):
        transaction.completion = None
    replacement = manager.begin()
    with pytest.raises(RuntimeError, match="stale"):
        transaction.__exit__(None, None, None)
    assert transaction.completion is outcome
    assert replacement.completion is None
    manager.rollback()


def test_standalone_validation_does_not_finalize_or_create_evidence() -> None:
    manager = TransactionManager()
    transaction = manager.begin()
    manager.enlist(CompletionContext(name="A", require_validation=True))
    manager.validate()
    assert manager.active_transaction is transaction and transaction.completion is None
    manager.rollback()


def test_validation_failure_is_retained_before_discard_errors() -> None:
    manager = TransactionManager()
    validation = ValueError("validation failed")
    cleanup = RuntimeError("cleanup failed")
    context = CompletionContext(
        name="A",
        require_validation=True,
        errors={"validate": validation, "discard": cleanup},
    )
    transaction = manager.begin()
    manager.enlist(context)
    with pytest.raises(ExceptionGroup) as raised:
        manager.commit()
    assert raised.value.exceptions[0].exceptions == (validation,)
    assert raised.value.exceptions[1] is cleanup
    outcome = transaction.completion
    assert outcome.failures == raised.value.exceptions
    assert not outcome.publication_started and not outcome.discard_complete
    assert outcome.after_actions_complete and outcome.finalized


@pytest.mark.parametrize(
    "error", (KeyboardInterrupt("interrupted"), SystemExit("exiting"))
)
def test_system_exception_still_drains_mandatory_cleanup(error: BaseException) -> None:
    manager = TransactionManager()
    events: list[str] = []
    first = CompletionContext(name="A", events=events, errors={"discard": error})
    cleanup = ValueError("after failed")
    second = CompletionContext(
        name="B", events=events, errors={"after_rollback": cleanup}
    )
    transaction = manager.begin()
    manager.enlist(first)
    manager.enlist(second)
    with pytest.raises(BaseExceptionGroup) as raised:
        manager.rollback()
    assert raised.value.exceptions == (error, cleanup)
    assert transaction.completion.failures == (error, cleanup)
    assert events == ["discard:A", "discard:B", "after_rollback:B"]
    assert manager.active_transaction is None


def test_repeated_exception_keeps_identity_and_each_callback_note() -> None:
    manager = TransactionManager()
    failure = ValueError("shared failure")
    transaction = manager.begin()
    for name in ("A", "B"):
        manager.enlist(CompletionContext(name=name, errors={"after_commit": failure}))
    with pytest.raises(ValueError) as raised:
        manager.commit_only()
    assert raised.value is failure
    assert transaction.completion.failures == (failure,)
    assert len(failure.__notes__) == 2


@pytest.mark.parametrize(
    "phase",
    (
        "validate",
        "order",
        "prepare",
        "apply",
        "discard",
        "after_commit",
        "after_rollback",
    ),
)
@pytest.mark.parametrize("mutation", ("begin", "commit", "rollback", "enlist", "drop"))
def test_completion_guards_membership_and_reentry_before_mutation(
    phase: str, mutation: str
) -> None:
    manager = TransactionManager()
    context = CompletionContext(name="A", require_validation=True)
    transaction = manager.begin()
    manager.enlist(context)

    def attempt() -> None:
        with pytest.raises(RuntimeError, match="completing"):
            if mutation == "enlist":
                manager.enlist(context)
            elif mutation == "drop":
                manager.drop(context, transaction.tx_id)
            else:
                getattr(manager, mutation)()
        assert manager.active_transaction is transaction and manager.begin_count == 1
        assert tuple(transaction.dirty_contexts.values()) == (context,)

    context.actions[phase] = attempt
    if phase in {"discard", "after_rollback"}:
        manager.rollback()
    else:
        manager.commit()
    assert f"{phase}:A" in context.events
    assert transaction.completion.ownership_preserved


def test_other_key_completes_independently_after_a_key_failure() -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA, GROUP_BETA))
    alpha = manager.begin(GROUP_ALPHA)
    beta = manager.begin(GROUP_BETA)
    failure = ValueError("alpha failed")
    manager.enlist(CompletionContext(name="A", errors={"apply": failure}), GROUP_ALPHA)
    manager.enlist(CompletionContext(name="B"), GROUP_BETA)
    with pytest.raises(ValueError) as raised:
        manager.commit_only(GROUP_ALPHA, GROUP_BETA)
    assert raised.value is failure
    assert not alpha.completion.publication_complete
    assert beta.completion.publication_complete
    assert manager.active_transaction_for(GROUP_ALPHA) is None
    assert manager.active_transaction_for(GROUP_BETA) is None


@pytest.mark.parametrize("method", ("commit_only", "rollback"))
def test_required_missing_callback_is_a_failure_but_optional_absence_is_not(
    method: str,
) -> None:
    class MissingCallbacks:
        def requires_validation_for(self, tx_key: object) -> bool:
            return False

        def commit_order_key_for(self, tx_key: object) -> tuple[object, ...]:
            return ()

    manager = TransactionManager()
    transaction = manager.begin()
    manager.enlist(MissingCallbacks())
    with pytest.raises((AttributeError, ExceptionGroup)):
        getattr(manager, method)()
    outcome = transaction.completion
    assert not outcome.publication_complete and not outcome.discard_complete
    assert outcome.after_actions_complete and outcome.finalized
    assert all("callback" in str(error) for error in outcome.failures)


def test_scope_body_failure_is_not_replaced_by_rollback_failure() -> None:
    manager = TransactionManager()
    body = ValueError("body failed")
    cleanup = RuntimeError("cleanup failed")
    with pytest.raises(ExceptionGroup) as raised:
        with manager.begin() as transaction:
            manager.enlist(CompletionContext(name="A", errors={"discard": cleanup}))
            raise body
    assert raised.value.exceptions == (body, cleanup)
    assert transaction.completion.failures == (cleanup,)


def test_fixed_completion_order_does_not_recompute_callback_keys() -> None:
    manager = TransactionManager()
    events: list[str] = []
    contexts = [
        CompletionContext(name="low", rank=(1,), events=events),
        CompletionContext(name="first_high", rank=(2,), events=events),
        CompletionContext(name="second_high", rank=(2,), events=events),
    ]
    transaction = manager.begin()
    for context in contexts:
        manager.enlist(context)
        context.actions["prepare"] = lambda context=context: setattr(
            context, "rank", (100,)
        )
    manager.commit_only()
    assert events == [
        "order:low",
        "order:first_high",
        "order:second_high",
        "prepare:first_high",
        "prepare:second_high",
        "prepare:low",
        "apply:first_high",
        "apply:second_high",
        "apply:low",
        "after_commit:first_high",
        "after_commit:second_high",
        "after_commit:low",
    ]
    assert transaction.completion.publication_complete


@pytest.mark.parametrize("method", ("commit_only", "rollback"))
def test_legacy_required_callbacks_work_without_optional_callbacks(method: str) -> None:
    events: list[tuple[str, int, object]] = []

    class LegacyContext:
        def requires_validation_for(self, tx_key: object) -> bool:
            return False

        def commit_order_key_for(self, tx_key: object) -> tuple[object, ...]:
            return ()

        def _commit_transaction(self, tx_id: int, tx_key: object) -> None:
            events.append(("apply", tx_id, tx_key))

        def _rollback_transaction(self, tx_id: int, tx_key: object) -> None:
            events.append(("discard", tx_id, tx_key))

    manager = TransactionManager()
    transaction = manager.begin()
    manager.enlist(LegacyContext())
    assert getattr(manager, method)() == transaction.tx_id
    assert events == [
        (
            "apply" if method == "commit_only" else "discard",
            transaction.tx_id,
            transaction.tx_key,
        )
    ]
    assert transaction.completion.after_actions_complete


def test_validation_cannot_certify_or_discard_a_replacement_token() -> None:
    manager = TransactionManager()
    original = manager.begin()
    replacement = LifecycleTransaction(tx_id=original.tx_id + 1)
    failure = ValueError("validator failed after replacing token")
    context = CompletionContext(
        name="A",
        require_validation=True,
        errors={"validate": failure},
        actions={
            "validate": lambda: setattr(manager, "active_transaction", replacement)
        },
    )
    manager.enlist(context)
    with pytest.raises(ExceptionGroup) as raised:
        manager.commit()
    assert raised.value.exceptions[0].exceptions == (failure,)
    assert isinstance(raised.value.exceptions[1], RuntimeError)
    assert context.events == ["validate:A"]
    assert manager.active_transaction is replacement
    outcome = original.completion
    assert not outcome.ownership_preserved and not outcome.finalized
    assert not outcome.publication_started and not outcome.discard_complete
    assert not outcome.after_actions_complete
    assert replacement.completion is None
    manager.rollback()


def test_unsupported_direct_membership_mutation_prevents_certification() -> None:
    manager = TransactionManager()
    transaction = manager.begin()
    context = CompletionContext(
        name="A", actions={"prepare": transaction.dirty_contexts.clear}
    )
    manager.enlist(context)
    with pytest.raises(RuntimeError, match="membership changed"):
        manager.commit_only()
    outcome = transaction.completion
    assert not outcome.ownership_preserved and outcome.finalized
    assert not outcome.publication_started and not outcome.discard_complete
    assert context.events == ["order:A", "prepare:A"]
    assert manager.active_transaction is None


def test_nested_hook_group_and_repeated_leaf_keep_one_original_failure() -> None:
    manager = TransactionManager()
    original = ValueError("same original error")
    hook_group = ExceptionGroup("hook failures", [original])
    transaction = manager.begin()
    manager.enlist(CompletionContext(name="A", errors={"after_commit": hook_group}))
    manager.enlist(CompletionContext(name="B", errors={"after_commit": original}))
    with pytest.raises(ExceptionGroup) as raised:
        manager.commit_only()
    assert raised.value is hook_group
    assert transaction.completion.failures == (hook_group,)
    assert len(original.__notes__) == 1


def test_multi_key_scope_preserves_body_once_and_drains_system_exception_cleanup() -> (
    None
):
    manager = TransactionManager(tx_keys=(GROUP_ALPHA, GROUP_BETA))
    body = ValueError("body failed")
    alpha_error = KeyboardInterrupt("alpha cleanup interrupted")
    beta_error = RuntimeError("beta cleanup failed")
    with pytest.raises(BaseExceptionGroup) as raised:
        with manager.begin(GROUP_ALPHA, GROUP_BETA) as scope:
            manager.enlist(
                CompletionContext(name="A", errors={"discard": alpha_error}),
                GROUP_ALPHA,
            )
            manager.enlist(
                CompletionContext(name="B", errors={"discard": beta_error}), GROUP_BETA
            )
            raise body
    assert raised.value.exceptions == (body, beta_error, alpha_error)
    assert all(transaction.completion.finalized for transaction in scope.transactions)
    assert manager.active_transaction_for(GROUP_ALPHA) is None
    assert manager.active_transaction_for(GROUP_BETA) is None


def test_other_key_can_complete_inside_a_completion_callback() -> None:
    manager = TransactionManager(tx_keys=(GROUP_ALPHA,))
    other = manager.begin(GROUP_ALPHA)
    manager.enlist(CompletionContext(name="other"), GROUP_ALPHA)
    original = manager.begin(DEFAULT_TRANSACTION)
    context = CompletionContext(
        name="default",
        actions={"after_commit": lambda: manager.commit_only(GROUP_ALPHA)},
    )
    manager.enlist(context, DEFAULT_TRANSACTION)
    manager.commit_only(DEFAULT_TRANSACTION)
    assert (
        original.completion.publication_complete
        and other.completion.publication_complete
    )
    assert (
        original.completion.ownership_preserved and other.completion.ownership_preserved
    )


@pytest.mark.parametrize("invalid_window", ("wrong_token", "other", "nested", "reopen"))
def test_before_hook_window_rejects_invalid_or_repeated_entry(
    invalid_window: str,
) -> None:
    manager = TransactionManager()
    transaction = manager.begin()
    context = CompletionContext(name="preparing")
    other = CompletionContext(name="other")
    manager.enlist(context)

    def prepare() -> None:
        def open_window(participant: object = context, token: int = transaction.tx_id):
            return manager._before_commit_hooks(participant, DEFAULT_TRANSACTION, token)

        if invalid_window == "wrong_token":
            with pytest.raises(RuntimeError, match="invalid.*hook window"):
                with open_window(token=transaction.tx_id + 1):
                    pytest.fail("a stale token opened the write window")
        elif invalid_window == "other":
            with pytest.raises(RuntimeError, match="invalid.*hook window"):
                with open_window(other):
                    pytest.fail("another participant opened the write window")
        elif invalid_window == "nested":
            with open_window():
                with pytest.raises(RuntimeError, match="invalid.*hook window"):
                    with open_window():
                        pytest.fail("the hook window was entered recursively")
        else:
            with open_window():
                pass
            with pytest.raises(RuntimeError, match="invalid.*hook window"):
                with open_window():
                    pytest.fail("field preparation's write boundary was reopened")

    context.actions["prepare"] = prepare
    manager.commit_only()


def test_before_hook_failure_closes_legacy_candidate_write_permission() -> None:
    manager = TransactionManager()
    transaction = manager.begin()
    context = CompletionContext(name="preparing")
    failure = ValueError("before hook failed")
    manager.enlist(context)

    def prepare() -> None:
        with manager._before_commit_hooks(
            context, DEFAULT_TRANSACTION, transaction.tx_id
        ):
            raise failure

    def discard() -> None:
        with pytest.raises(RuntimeError, match="candidate write"):
            manager._require_candidate_write(context)

    context.actions.update(prepare=prepare, discard=discard)
    with pytest.raises(ValueError) as caught:
        manager.commit_only()
    assert caught.value is failure
