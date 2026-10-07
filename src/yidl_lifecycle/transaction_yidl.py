from __future__ import annotations

from collections.abc import Callable
from collections.abc import Hashable
from collections.abc import Iterable
from collections.abc import Iterator
from contextlib import AbstractContextManager
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from typing import Protocol
from typing import TypeAlias

DEFAULT_TRANSACTION: Hashable = "default_transaction"


class TransactionContext(Protocol):
    def commit_order_key_for(
        self, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> tuple[object, ...]: ...

    def requires_validation_for(
        self, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> bool: ...

    def validate_commit_for(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> bool: ...

    def _prepare_commit_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object: ...

    def _apply_prepared_commit_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object: ...

    def _after_commit_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object: ...

    def _rollback_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object: ...

    def _after_rollback_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object: ...


class YidlValidatorReturnedFalse(RuntimeError):
    """Raised when a context's validate_commit hook returns False."""

    def __init__(self, context: TransactionContext) -> None:
        self.context = context
        super().__init__(
            f"validate_commit returned False for {type(context).__qualname__!r}",
        )


@dataclass(frozen=True, slots=True)
class TransactionCompletion:
    tx_key: Hashable
    tx_id: int
    publication_started: bool
    publication_complete: bool
    discard_complete: bool
    after_actions_complete: bool
    ownership_preserved: bool
    finalized: bool
    failures: tuple[BaseException, ...]


def _unique_failures(failures: Iterable[BaseException]) -> tuple[BaseException, ...]:
    seen: set[int] = set()

    def leaf_ids(error: BaseException) -> Iterable[int]:
        if isinstance(error, BaseExceptionGroup):
            for child in error.exceptions:
                yield from leaf_ids(child)
        else:
            yield id(error)

    def keep(error: BaseException) -> bool:
        if isinstance(error, BaseExceptionGroup):
            ids = tuple(leaf_ids(error))
            distinct = set(ids)
            if len(ids) != len(distinct) or not distinct.isdisjoint(seen):
                return False
            seen.update(distinct)
            return True
        if id(error) in seen:
            return False
        seen.add(id(error))
        return True

    unique: list[BaseException] = []
    for error in failures:
        # Preserve hook-group provenance while excluding leaves already reported.
        retained = (
            error.subgroup(keep)
            if isinstance(error, BaseExceptionGroup)
            else error if keep(error) else None
        )
        if retained is not None:
            unique.append(retained)
    return tuple(unique)


def _raise_failures(message: str, failures: Iterable[BaseException]) -> None:
    unique = _unique_failures(failures)
    if len(unique) == 1:
        raise unique[0]
    if unique:
        raise BaseExceptionGroup(message, unique)


@dataclass(slots=True)
class LifecycleTransaction:
    tx_id: int
    tx_key: Hashable = DEFAULT_TRANSACTION
    _original_tx_id: int = field(init=False, repr=False, compare=False)
    _original_tx_key: Hashable = field(init=False, repr=False, compare=False)
    dirty_contexts: dict[int, TransactionContext] = field(default_factory=dict)
    validator_contexts: dict[int, TransactionContext] = field(default_factory=dict)
    _scope_commit: Callable[[], object] | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _scope_rollback: Callable[[], object] | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _completion: TransactionCompletion | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        self._original_tx_id = self.tx_id
        self._original_tx_key = self.tx_key

    @property
    def completion(self) -> TransactionCompletion | None:
        """Terminal evidence for this token, retained after manager finalization."""
        return self._completion

    def commit_order(self) -> tuple[TransactionContext, ...]:
        contexts = list(self.dirty_contexts.values())
        contexts.sort(
            key=lambda context: context.commit_order_key_for(self.tx_key), reverse=True
        )
        return tuple(contexts)

    def rollback_dirty(self) -> None:
        for context in list(self.dirty_contexts.values()):
            rollback = getattr(context, "_rollback_tx_by_key", None)
            if rollback is not None:
                rollback(self.tx_key, self.tx_id)
                continue
            legacy_rollback = getattr(context, "_rollback_transaction", None)
            if legacy_rollback is not None:
                legacy_rollback(self.tx_id, self.tx_key)
                continue
            raise AttributeError(
                f"{type(context).__qualname__!r} has no yidl rollback callback",
            )

    def after_rollbacks(self) -> None:
        for context in list(self.dirty_contexts.values()):
            after_rollback = getattr(context, "_after_rollback_tx_by_key", None)
            if after_rollback is not None:
                after_rollback(self.tx_key, self.tx_id)

    def validate_commit(self) -> None:
        failures: list[BaseException] = []
        for context in tuple(self.validator_contexts.values()):
            try:
                ok = context.validate_commit_for(self.tx_key)
            except BaseException as exc:
                failures.append(exc)
                continue
            if not ok:
                failures.append(YidlValidatorReturnedFalse(context))
        if failures:
            raise BaseExceptionGroup("yidl commit validation failed", failures)

    def prepare_commits(self) -> None:
        for context in self.commit_order():
            prepare = getattr(context, "_prepare_commit_tx_by_key", None)
            if prepare is not None:
                prepare(self.tx_key, self.tx_id)

    def apply_prepared_commits(self) -> None:
        for context in self.commit_order():
            apply_prepared = getattr(context, "_apply_prepared_commit_tx_by_key", None)
            if apply_prepared is not None:
                apply_prepared(self.tx_key, self.tx_id)
                continue
            legacy_commit = getattr(context, "_commit_transaction", None)
            if legacy_commit is not None:
                legacy_commit(self.tx_id, self.tx_key)
                continue
            raise AttributeError(
                f"{type(context).__qualname__!r} has no yidl commit callback",
            )

    def after_commits(self) -> None:
        for context in self.commit_order():
            after_commit = getattr(context, "_after_commit_tx_by_key", None)
            if after_commit is not None:
                after_commit(self.tx_key, self.tx_id)

    def bind_scope(
        self,
        *,
        commit: Callable[[], object],
        rollback: Callable[[], object],
    ) -> "LifecycleTransaction":
        self._scope_commit = commit
        self._scope_rollback = rollback
        return self

    def __enter__(self) -> "LifecycleTransaction":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> bool:
        del tb
        if self._scope_commit is None or self._scope_rollback is None:
            raise RuntimeError("yidl transaction scope is not bound")
        if exc_type is None:
            self._scope_commit()
        else:
            try:
                self._scope_rollback()
            except BaseException as cleanup:
                _raise_failures(
                    "yidl transaction body and rollback failed",
                    (cleanup,) if exc is None else (exc, cleanup),
                )
        return False


@dataclass(slots=True)
class _CompletionSession:
    manager: GroupTransactionManager
    transaction: LifecycleTransaction
    tx_id: int = field(init=False)
    tx_key: Hashable = field(init=False)
    participants: tuple[TransactionContext, ...] = field(init=False)
    validators: tuple[TransactionContext, ...] = field(init=False)
    begin_count: int = field(init=False)
    failures: list[BaseException] = field(default_factory=list, init=False)
    publication_started: bool = field(default=False, init=False)
    publication_complete: bool = field(default=False, init=False)
    discard_complete: bool = field(default=False, init=False)
    after_actions_complete: bool = field(default=False, init=False)
    ownership_preserved: bool = field(default=True, init=False)
    unprepared_ids: set[int] = field(init=False)
    preparing: TransactionContext | None = field(default=None, init=False)
    before_hook_context: TransactionContext | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.tx_id = self.transaction._original_tx_id
        self.tx_key = self.transaction._original_tx_key
        self.participants = tuple(self.transaction.dirty_contexts.values())
        self.validators = tuple(self.transaction.validator_contexts.values())
        self.begin_count = self.manager.begin_count
        self.unprepared_ids = {id(context) for context in self.participants}

    def require_candidate_write(self, context: TransactionContext) -> None:
        if (
            self.before_hook_context is None
            or id(context) not in self.unprepared_ids
            or not self._check_ownership()
        ):
            raise RuntimeError(
                "candidate write is not allowed while yidl transaction key is completing: "
                f"participant={type(context).__qualname__}, "
                f"tx_key={self.tx_key!r}, tx_id={self.tx_id}"
            )

    def _record(
        self,
        error: BaseException,
        phase: str,
        context: TransactionContext | None = None,
    ) -> None:
        self.failures[:] = _unique_failures((*self.failures, error))
        # Diagnostics must not interrupt cleanup or replace the retained failure.
        try:
            participant = "manager" if context is None else type(context).__qualname__
            BaseException.add_note(
                error,
                f"yidl completion phase={phase}, participant={participant}, "
                f"tx_key={self.tx_key!r}, tx_id={self.tx_id}",
            )
        except BaseException:
            pass

    def _check_ownership(self) -> bool:
        if not self.ownership_preserved:
            return False
        transaction = self.transaction
        dirty = tuple(transaction.dirty_contexts.values())
        validators = tuple(transaction.validator_contexts.values())
        preserved = (
            self.manager.active_transaction is transaction
            and type(transaction.tx_id) is int
            and transaction.tx_id == self.tx_id
            and transaction.tx_key is self.tx_key
            and self.manager.tx_key is self.tx_key
            and self.manager.begin_count == self.begin_count
            and len(dirty) == len(self.participants)
            and all(
                actual is expected for actual, expected in zip(dirty, self.participants)
            )
            and len(validators) == len(self.validators)
            and all(
                actual is expected
                for actual, expected in zip(validators, self.validators)
            )
        )
        if not preserved:
            self.ownership_preserved = False
            self._record(
                RuntimeError(
                    "owned yidl transaction identity or completion membership changed"
                ),
                "ownership",
            )
        return preserved

    def _attempt(
        self,
        phase: str,
        context: TransactionContext,
        method: str,
        *,
        legacy: str | None = None,
        required: bool = False,
        publishes: bool = False,
    ) -> bool:
        if not self._check_ownership():
            return False
        succeeded = False
        try:
            callback = getattr(context, method, None)
            if callback is not None:
                if publishes:
                    self.publication_started = True
                callback(self.tx_key, self.tx_id)
            elif (
                legacy is not None
                and (callback := getattr(context, legacy, None)) is not None
            ):
                if publishes:
                    self.publication_started = True
                callback(self.tx_id, self.tx_key)
            elif required:
                raise AttributeError(
                    f"{type(context).__qualname__!r} has no yidl {phase} callback"
                )
            succeeded = True
        except BaseException as error:
            self._record(error, phase, context)
        self._check_ownership()
        return succeeded

    def _validate(self) -> bool:
        failures: list[BaseException] = []
        first_failure_index = len(self.failures)
        for context in self.validators:
            if not self._check_ownership():
                break
            try:
                if not context.validate_commit_for(self.tx_key):
                    raise YidlValidatorReturnedFalse(context)
            except BaseException as error:
                if not any(previous is error for previous in failures):
                    failures.append(error)
                try:
                    BaseException.add_note(
                        error,
                        f"yidl validator participant={type(context).__qualname__}, "
                        f"tx_key={self.tx_key!r}, tx_id={self.tx_id}",
                    )
                except BaseException:
                    pass
            self._check_ownership()
        if failures:
            self._record(
                BaseExceptionGroup("yidl commit validation failed", failures),
                "validate",
            )
            # Validation remains the primary failure if its callback also lost ownership.
            self.failures.insert(first_failure_index, self.failures.pop())
        return not failures and self.ownership_preserved

    def _commit_order(self) -> tuple[TransactionContext, ...] | None:
        keys: list[tuple[tuple[object, ...], TransactionContext]] = []
        for context in self.participants:
            if not self._check_ownership():
                return None
            try:
                keys.append((context.commit_order_key_for(self.tx_key), context))
            except BaseException as error:
                self._record(error, "order", context)
                self._check_ownership()
                return None
            if not self._check_ownership():
                return None
        try:
            keys.sort(key=lambda item: item[0], reverse=True)
        except BaseException as error:
            self._record(error, "order")
            self._check_ownership()
            return None
        return (
            tuple(context for _, context in keys) if self._check_ownership() else None
        )

    def _discard(self, contexts: tuple[TransactionContext, ...]) -> set[int]:
        if not self._check_ownership():
            return set()
        discarded: set[int] = set()
        for context in contexts:
            if self._attempt(
                "discard",
                context,
                "_rollback_tx_by_key",
                legacy="_rollback_transaction",
                required=True,
            ):
                discarded.add(id(context))
        self.discard_complete = len(discarded) == len(contexts)
        return discarded

    def _after(
        self,
        contexts: tuple[TransactionContext, ...],
        applied: set[int],
        discarded: set[int],
    ) -> None:
        if not self._check_ownership():
            return
        complete = True
        for context in contexts:
            if id(context) in applied:
                succeeded = self._attempt(
                    "after_commit", context, "_after_commit_tx_by_key"
                )
            elif id(context) in discarded:
                succeeded = self._attempt(
                    "after_rollback", context, "_after_rollback_tx_by_key"
                )
            else:
                continue
            complete = succeeded and complete
        self.after_actions_complete = complete

    def rollback(self) -> None:
        discarded = self._discard(self.participants)
        self._after(self.participants, set(), discarded)

    def commit(self, *, validate: bool) -> None:
        if validate and not self._validate():
            self.rollback()
            return
        ordered = self._commit_order()
        if ordered is None:
            self.rollback()
            return
        for context in ordered:
            self.preparing = context
            try:
                prepared = self._attempt(
                    "prepare", context, "_prepare_commit_tx_by_key"
                )
            finally:
                self.before_hook_context = None
                self.unprepared_ids.discard(id(context))
                self.preparing = None
            if not prepared or not self.ownership_preserved:
                self.rollback()
                return
        applied: set[int] = set()
        for context in ordered:
            if not self._check_ownership():
                break
            if self._attempt(
                "apply",
                context,
                "_apply_prepared_commit_tx_by_key",
                legacy="_commit_transaction",
                required=True,
                publishes=True,
            ):
                applied.add(id(context))
        self.publication_complete = len(applied) == len(ordered)
        failed = tuple(context for context in ordered if id(context) not in applied)
        discarded = self._discard(failed) if failed else set()
        self._after(ordered, applied, discarded)

    def finalize(self) -> None:
        self._check_ownership()
        finalized = self.manager.active_transaction is self.transaction
        if finalized:
            self.manager.active_transaction = None
            self.manager.begin_count = 0
        self.manager._completing = False
        self.manager._completion_session = None
        self.transaction._completion = TransactionCompletion(
            tx_key=self.tx_key,
            tx_id=self.tx_id,
            publication_started=self.publication_started,
            publication_complete=self.publication_complete,
            discard_complete=self.discard_complete,
            after_actions_complete=self.after_actions_complete,
            ownership_preserved=self.ownership_preserved,
            finalized=finalized,
            failures=tuple(self.failures),
        )


@dataclass(slots=True)
class GroupTransactionManager:
    tx_key: Hashable = DEFAULT_TRANSACTION
    _next_tx_id: int = field(default=1, init=False, repr=False)
    active_transaction: LifecycleTransaction | None = field(
        default=None, init=False, repr=False
    )
    begin_count: int = field(default=0, init=False, repr=False)
    _completing: bool = field(default=False, init=False, repr=False)
    _completion_session: _CompletionSession | None = field(
        default=None, init=False, repr=False
    )

    def active_transaction_for(
        self, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> LifecycleTransaction | None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        return self.active_transaction

    def begin(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> LifecycleTransaction:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        self._require_not_completing()
        if self.begin_count == 0:
            if self.active_transaction is not None:
                raise RuntimeError("yidl transaction manager state is corrupted")
            self.active_transaction = LifecycleTransaction(
                tx_id=self._next_tx_id, tx_key=self.tx_key
            )
            self._next_tx_id += 1
        self.begin_count += 1
        transaction = self.active_transaction
        assert transaction is not None
        return transaction.bind_scope(
            commit=lambda: self._commit_scope(transaction),
            rollback=lambda: self._rollback_scope(transaction),
        )

    def _require_not_completing(self) -> None:
        if self._completing:
            transaction = self.active_transaction
            token = None if transaction is None else transaction.tx_id
            raise RuntimeError(
                f"yidl transaction key is completing: tx_key={self.tx_key!r}, tx_id={token}"
            )

    def _require_candidate_write(
        self, context: TransactionContext, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        if self.active_transaction is None:
            raise RuntimeError("writes require an active yidl transaction")
        if self._completing:
            session = self._completion_session
            if session is None:
                raise RuntimeError("yidl completion session is missing")
            session.require_candidate_write(context)

    @contextmanager
    def _before_commit_hooks(
        self, context: TransactionContext, tx_key: Hashable, tx_token: int | None
    ) -> Iterator[None]:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        session = self._completion_session
        if (
            not self._completing
            or session is None
            or session.preparing is not context
            or session.before_hook_context is not None
            or id(context) not in session.unprepared_ids
            or session.tx_id != tx_token
            or not session._check_ownership()
        ):
            raise RuntimeError("invalid yidl before-commit hook window")
        session.before_hook_context = context
        try:
            yield
        finally:
            session.before_hook_context = None
            session.unprepared_ids.discard(id(context))

    def _require_current(self, transaction: LifecycleTransaction) -> None:
        if self.active_transaction is not transaction:
            raise RuntimeError("owned yidl transaction is missing or replaced")
        if (
            type(transaction.tx_id) is not int
            or transaction.tx_id != transaction._original_tx_id
            or transaction.tx_key is not transaction._original_tx_key
        ):
            raise RuntimeError("owned yidl transaction identity changed")

    def require_sole_transaction_owner(self, transaction: LifecycleTransaction) -> None:
        """Check ownership without validating, publishing, or changing nesting."""
        if transaction.tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {transaction.tx_key!r}")
        self._require_not_completing()
        self._require_current(transaction)
        if self.begin_count != 1:
            raise RuntimeError("yidl transaction acquired an external nested begin")

    def _commit_scope(self, transaction: LifecycleTransaction) -> int | None:
        if self.active_transaction is not transaction:
            raise RuntimeError("stale yidl transaction scope cannot commit")
        return self.commit(self.tx_key)

    def _rollback_scope(self, transaction: LifecycleTransaction) -> int | None:
        # A nested failure may already have discarded this whole transaction.
        # Its enclosing exceptional exits must preserve the original exception.
        if self.active_transaction is not transaction:
            return None
        return self.rollback(self.tx_key)

    def validate(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        self._require_not_completing()
        if self.begin_count <= 0:
            raise RuntimeError("no active yidl transaction")
        transaction = self.active_transaction
        if transaction is None:
            raise RuntimeError("yidl transaction manager state is corrupted")
        self._require_current(transaction)
        transaction.validate_commit()

    def commit_only(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> int | None:
        return self._complete_commit(tx_key, validate=False)

    def _complete_commit(self, tx_key: Hashable, *, validate: bool) -> int | None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        self._require_not_completing()
        if self.begin_count <= 0:
            raise RuntimeError("no active yidl transaction")
        if self.begin_count > 1:
            self.begin_count -= 1
            return None
        transaction = self.active_transaction
        if transaction is None:
            raise RuntimeError("yidl transaction manager state is corrupted")
        session = _CompletionSession(self, transaction)
        self._completing = True
        self._completion_session = session
        try:
            session.commit(validate=validate)
        finally:
            session.finalize()
        _raise_failures("yidl transaction completion failed", session.failures)
        return session.tx_id

    def commit(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> int | None:
        return self._complete_commit(tx_key, validate=True)

    def rollback(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> int | None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        self._require_not_completing()
        if self.begin_count <= 0 or self.active_transaction is None:
            raise RuntimeError("no active yidl transaction")
        transaction = self.active_transaction
        session = _CompletionSession(self, transaction)
        self._completing = True
        self._completion_session = session
        try:
            session.rollback()
        finally:
            session.finalize()
        _raise_failures("yidl transaction rollback failed", session.failures)
        return session.tx_id

    def enlist(
        self, context: TransactionContext, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> int:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        transaction = self.active_transaction
        if transaction is None:
            raise RuntimeError("no active yidl transaction")
        context_id = id(context)
        if self._completing:
            self._require_candidate_write(context, tx_key)
            if transaction.dirty_contexts.get(context_id) is not context:
                raise RuntimeError(
                    "cannot enlist a new participant during yidl completion"
                )
            return transaction.tx_id
        transaction.dirty_contexts[context_id] = context
        if context.requires_validation_for(tx_key):
            transaction.validator_contexts[context_id] = context
        return transaction.tx_id

    def drop(
        self,
        context: TransactionContext,
        tx_id: int | None = None,
        tx_key: Hashable = DEFAULT_TRANSACTION,
    ) -> None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        self._require_not_completing()
        transaction = self.active_transaction
        if transaction is None:
            return
        if tx_id is not None and transaction.tx_id != tx_id:
            return
        context_id = id(context)
        transaction.dirty_contexts.pop(context_id, None)
        transaction.validator_contexts.pop(context_id, None)


@dataclass(slots=True, frozen=True)
class _MultiGroupTransactionScope:
    transactions: tuple[LifecycleTransaction, ...]

    def __enter__(self) -> "_MultiGroupTransactionScope":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> bool:
        failures: list[BaseException] = []
        for transaction in reversed(self.transactions):
            try:
                transaction.__exit__(exc_type, None, tb)
            except BaseException as error:
                failures.append(error)
                try:
                    BaseException.add_note(
                        error,
                        f"yidl scope tx_key={transaction._original_tx_key!r}, "
                        f"tx_id={transaction._original_tx_id}",
                    )
                except BaseException:
                    pass
        if failures:
            _raise_failures(
                "yidl transaction scope completion failed",
                failures if exc is None else (exc, *failures),
            )
        return False


CommitResult: TypeAlias = int | tuple[int | None, ...] | None


class TransactionManager:
    __slots__ = ("_tx_keys", "_tx_key_set", "_group_managers")

    def __init__(self, *, tx_keys: Iterable[Hashable] = ()) -> None:
        normalized_groups: list[Hashable] = []
        seen = {DEFAULT_TRANSACTION}
        for group in tx_keys:
            if group in seen:
                continue
            seen.add(group)
            normalized_groups.append(group)
        self._tx_keys = tuple(normalized_groups)
        self._tx_key_set = frozenset((DEFAULT_TRANSACTION, *self._tx_keys))
        self._group_managers: dict[Hashable, GroupTransactionManager] = {}

    @property
    def tx_keys(self) -> tuple[Hashable, ...]:
        return self._tx_keys

    @property
    def active_transaction(self) -> LifecycleTransaction | None:
        return self._get_group_manager(DEFAULT_TRANSACTION).active_transaction

    @active_transaction.setter
    def active_transaction(self, value: LifecycleTransaction | None) -> None:
        self._get_group_manager(DEFAULT_TRANSACTION).active_transaction = value

    @property
    def begin_count(self) -> int:
        return self._get_group_manager(DEFAULT_TRANSACTION).begin_count

    def active_transaction_for(
        self, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> LifecycleTransaction | None:
        return self._get_group_manager(tx_key).active_transaction

    def require_sole_transaction_owner(self, transaction: LifecycleTransaction) -> None:
        """Require this token to own its key with exactly one outstanding begin."""
        self._get_group_manager(
            transaction._original_tx_key
        ).require_sole_transaction_owner(transaction)

    def _require_candidate_write(
        self, context: TransactionContext, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> None:
        self._get_group_manager(tx_key)._require_candidate_write(context, tx_key)

    def _before_commit_hooks(
        self, context: TransactionContext, tx_key: Hashable, tx_token: int | None
    ) -> AbstractContextManager[None]:
        return self._get_group_manager(tx_key)._before_commit_hooks(
            context, tx_key, tx_token
        )

    def _normalize_groups(self, groups: tuple[Hashable, ...]) -> tuple[Hashable, ...]:
        if not groups:
            return (DEFAULT_TRANSACTION, *self._tx_keys)
        normalized: list[Hashable] = []
        seen: set[Hashable] = set()
        for group in groups:
            self._require_known_group(group)
            if group in seen:
                continue
            seen.add(group)
            normalized.append(group)
        return tuple(normalized)

    def _require_known_group(self, group: Hashable) -> None:
        if group not in self._tx_key_set:
            raise RuntimeError(f"unknown yidl transaction key {group!r}")

    def _get_group_manager(self, group: Hashable) -> GroupTransactionManager:
        self._require_known_group(group)
        manager = self._group_managers.get(group)
        if manager is None:
            manager = GroupTransactionManager(tx_key=group)
            self._group_managers[group] = manager
        return manager

    def begin(
        self, *groups: Hashable
    ) -> LifecycleTransaction | _MultiGroupTransactionScope:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).begin(
                normalized_groups[0]
            )
        managers = tuple(self._get_group_manager(group) for group in normalized_groups)
        for manager in managers:
            manager._require_not_completing()
        transactions = tuple(manager.begin(manager.tx_key) for manager in managers)
        return _MultiGroupTransactionScope(transactions)

    def validate(self, *groups: Hashable) -> None:
        normalized_groups = self._normalize_groups(groups)
        failures: list[BaseException] = []
        for group in normalized_groups:
            try:
                self._get_group_manager(group).validate(group)
            except BaseException as exc:
                failures.append(exc)
        if not failures:
            return
        _raise_failures("yidl transaction key validation failed", failures)

    def commit_only(self, *groups: Hashable) -> CommitResult:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).commit_only(
                normalized_groups[0]
            )
        failures: list[BaseException] = []
        results: list[int | None] = []
        for group in normalized_groups:
            try:
                results.append(self._get_group_manager(group).commit_only(group))
            except BaseException as exc:
                failures.append(exc)
        if failures:
            _raise_failures("yidl transaction key commit_only failed", failures)
        return tuple(results)

    def commit(self, *groups: Hashable) -> CommitResult:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).commit(
                normalized_groups[0]
            )
        failures: list[BaseException] = []
        results: list[int | None] = []
        for group in normalized_groups:
            try:
                results.append(self._get_group_manager(group).commit(group))
            except BaseException as exc:
                failures.append(exc)
        if failures:
            _raise_failures("yidl transaction key commit failed", failures)
        return tuple(results)

    def rollback(self, *groups: Hashable) -> CommitResult:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).rollback(
                normalized_groups[0]
            )
        failures: list[BaseException] = []
        results: list[int | None] = []
        for group in normalized_groups:
            try:
                results.append(self._get_group_manager(group).rollback(group))
            except BaseException as exc:
                failures.append(exc)
        if failures:
            _raise_failures("yidl transaction key rollback failed", failures)
        return tuple(results)

    def enlist(
        self, context: TransactionContext, tx_key: Hashable = DEFAULT_TRANSACTION
    ) -> int:
        return self._get_group_manager(tx_key).enlist(context, tx_key)

    def drop(
        self,
        context: TransactionContext,
        tx_id: int | None = None,
        tx_key: Hashable = DEFAULT_TRANSACTION,
    ) -> None:
        self._get_group_manager(tx_key).drop(context, tx_id, tx_key)
