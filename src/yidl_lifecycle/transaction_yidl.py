from __future__ import annotations

from collections.abc import Callable
from collections.abc import Hashable
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import Protocol
from typing import TypeAlias


DEFAULT_TRANSACTION: Hashable = "default_transaction"


class TransactionContext(Protocol):
    def commit_order_key_for(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> tuple[object, ...]:
        ...

    def requires_validation_for(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> bool:
        ...

    def validate_commit_for(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> bool:
        ...

    def _prepare_commit_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        ...

    def _apply_prepared_commit_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        ...

    def _after_commit_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        ...

    def _rollback_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        ...

    def _after_rollback_tx_by_key(
        self,
        tx_key: Hashable = DEFAULT_TRANSACTION,
        tx_token: int | None = None,
    ) -> object:
        ...


class YidlValidatorReturnedFalse(RuntimeError):
    """Raised when a context's validate_commit hook returns False."""

    def __init__(self, context: TransactionContext) -> None:
        self.context = context
        super().__init__(
            f"validate_commit returned False for {type(context).__qualname__!r}",
        )


@dataclass(slots=True)
class LifecycleTransaction:
    tx_id: int
    tx_key: Hashable = DEFAULT_TRANSACTION
    dirty_contexts: dict[int, TransactionContext] = field(default_factory=dict)
    validator_contexts: dict[int, TransactionContext] = field(default_factory=dict)
    _scope_commit: Callable[[], object] | None = field(default=None, init=False, repr=False, compare=False)
    _scope_rollback: Callable[[], object] | None = field(default=None, init=False, repr=False, compare=False)

    def commit_order(self) -> tuple[TransactionContext, ...]:
        contexts = list(self.dirty_contexts.values())
        contexts.sort(key=lambda context: context.commit_order_key_for(self.tx_key), reverse=True)
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
        for context in self.validator_contexts.values():
            try:
                ok = context.validate_commit_for(self.tx_key)
            except BaseException as exc:
                failures.append(exc)
                continue
            if not ok:
                failures.append(YidlValidatorReturnedFalse(context))
        if failures:
            raise ExceptionGroup("yidl commit validation failed", failures)

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
        del exc, tb
        if self._scope_commit is None or self._scope_rollback is None:
            raise RuntimeError("yidl transaction scope is not bound")
        if exc_type is None:
            self._scope_commit()
        else:
            self._scope_rollback()
        return False


@dataclass(slots=True)
class GroupTransactionManager:
    tx_key: Hashable = DEFAULT_TRANSACTION
    _next_tx_id: int = field(default=1, init=False, repr=False)
    active_transaction: LifecycleTransaction | None = field(default=None, init=False, repr=False)
    begin_count: int = field(default=0, init=False, repr=False)
    _completing: bool = field(default=False, init=False, repr=False)

    def active_transaction_for(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> LifecycleTransaction | None:
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
            self.active_transaction = LifecycleTransaction(tx_id=self._next_tx_id, tx_key=self.tx_key)
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
            raise RuntimeError("yidl transaction key is completing")

    def _require_current(self, transaction: LifecycleTransaction) -> None:
        if self.active_transaction is not transaction:
            raise RuntimeError("owned yidl transaction is missing or replaced")

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
        if self.begin_count <= 0:
            raise RuntimeError("no active yidl transaction")
        transaction = self.active_transaction
        if transaction is None:
            raise RuntimeError("yidl transaction manager state is corrupted")
        transaction.validate_commit()

    def commit_only(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> int | None:
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
        tx_id = transaction.tx_id
        self._completing = True
        try:
            try:
                transaction.prepare_commits()
            except BaseException:
                transaction.rollback_dirty()
                transaction.after_rollbacks()
                raise
            transaction.apply_prepared_commits()
            transaction.after_commits()
        finally:
            self.active_transaction = None
            self.begin_count = 0
            self._completing = False
        return tx_id

    def commit(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> int | None:
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
        try:
            self.validate(tx_key)
        except BaseException:
            if self.active_transaction is transaction:
                self.rollback(tx_key)
            raise
        self._require_current(transaction)
        return self.commit_only(tx_key)

    def rollback(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> int | None:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        self._require_not_completing()
        if self.begin_count <= 0 or self.active_transaction is None:
            raise RuntimeError("no active yidl transaction")
        transaction = self.active_transaction
        tx_id = transaction.tx_id
        self._completing = True
        try:
            transaction.rollback_dirty()
            transaction.after_rollbacks()
        finally:
            self.active_transaction = None
            self.begin_count = 0
            self._completing = False
        return tx_id

    def enlist(self, context: TransactionContext, tx_key: Hashable = DEFAULT_TRANSACTION) -> int:
        if tx_key != self.tx_key:
            raise RuntimeError(f"unknown yidl transaction key {tx_key!r}")
        transaction = self.active_transaction
        if transaction is None:
            raise RuntimeError("no active yidl transaction")
        context_id = id(context)
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
                transaction.__exit__(exc_type, exc, tb)
            except BaseException as error:
                failures.append(error)
        if len(failures) == 1:
            raise failures[0]
        if failures:
            raise BaseExceptionGroup("yidl transaction scope completion failed", failures)
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

    def active_transaction_for(self, tx_key: Hashable = DEFAULT_TRANSACTION) -> LifecycleTransaction | None:
        return self._get_group_manager(tx_key).active_transaction

    def require_sole_transaction_owner(self, transaction: LifecycleTransaction) -> None:
        """Require this token to own its key with exactly one outstanding begin."""
        self._get_group_manager(transaction.tx_key).require_sole_transaction_owner(transaction)

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

    def begin(self, *groups: Hashable) -> LifecycleTransaction | _MultiGroupTransactionScope:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).begin(normalized_groups[0])
        managers = tuple(self._get_group_manager(group) for group in normalized_groups)
        for manager in managers:
            manager._require_not_completing()
        transactions = tuple(
            manager.begin(manager.tx_key) for manager in managers
        )
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
        if len(failures) == 1:
            raise failures[0]
        raise ExceptionGroup("yidl transaction key validation failed", failures)

    def commit_only(self, *groups: Hashable) -> CommitResult:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).commit_only(normalized_groups[0])
        failures: list[BaseException] = []
        results: list[int | None] = []
        for group in normalized_groups:
            try:
                results.append(self._get_group_manager(group).commit_only(group))
            except BaseException as exc:
                failures.append(exc)
        if failures:
            if len(failures) == 1:
                raise failures[0]
            raise ExceptionGroup("yidl transaction key commit_only failed", failures)
        return tuple(results)

    def commit(self, *groups: Hashable) -> CommitResult:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).commit(normalized_groups[0])
        failures: list[BaseException] = []
        results: list[int | None] = []
        for group in normalized_groups:
            try:
                results.append(self._get_group_manager(group).commit(group))
            except BaseException as exc:
                failures.append(exc)
        if failures:
            if len(failures) == 1:
                raise failures[0]
            raise ExceptionGroup("yidl transaction key commit failed", failures)
        return tuple(results)

    def rollback(self, *groups: Hashable) -> CommitResult:
        normalized_groups = self._normalize_groups(groups)
        if len(normalized_groups) == 1:
            return self._get_group_manager(normalized_groups[0]).rollback(normalized_groups[0])
        failures: list[BaseException] = []
        results: list[int | None] = []
        for group in normalized_groups:
            try:
                results.append(self._get_group_manager(group).rollback(group))
            except BaseException as exc:
                failures.append(exc)
        if failures:
            if len(failures) == 1:
                raise failures[0]
            raise ExceptionGroup("yidl transaction key rollback failed", failures)
        return tuple(results)

    def enlist(self, context: TransactionContext, tx_key: Hashable = DEFAULT_TRANSACTION) -> int:
        return self._get_group_manager(tx_key).enlist(context, tx_key)

    def drop(
        self,
        context: TransactionContext,
        tx_id: int | None = None,
        tx_key: Hashable = DEFAULT_TRANSACTION,
    ) -> None:
        self._get_group_manager(tx_key).drop(context, tx_id, tx_key)
