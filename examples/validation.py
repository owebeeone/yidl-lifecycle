"""Validate candidates and distinguish rejection from an after-hook failure."""
from yidl_lifecycle.lifecycle import (
    after_commit,
    lifecycle,
    managed,
    validate_commit,
)
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager

events = []


@lifecycle
class Stock:
    quantity: int = managed(default=1)

    @validate_commit(DEFAULT_TRANSACTION)
    def valid_quantity(self) -> bool:
        return self.quantity >= 0

    @after_commit(DEFAULT_TRANSACTION)
    def notify(self) -> None:
        events.append(self.quantity)


manager = TransactionManager()
stock = Stock(transaction_manager=manager)
transaction = manager.begin(DEFAULT_TRANSACTION)
stock.quantity = -1
try:
    manager.commit(DEFAULT_TRANSACTION)
except ExceptionGroup:
    assert stock.quantity == 1
    assert transaction.completion.discard_complete
else:
    raise AssertionError("invalid quantity was accepted")
assert events == []

with manager.begin(DEFAULT_TRANSACTION):
    stock.quantity = 3
assert events == [3]


@lifecycle
class FailingNotification:
    value: int = managed(default=0)

    @after_commit(DEFAULT_TRANSACTION)
    def notify(self) -> None:
        raise ValueError("notification failed")


model = FailingNotification(transaction_manager=manager)
transaction = manager.begin(DEFAULT_TRANSACTION)
model.value = 4
try:
    manager.commit(DEFAULT_TRANSACTION)
except ValueError:
    evidence = transaction.completion
    assert evidence.publication_complete
    assert not evidence.after_actions_complete
    assert evidence.finalized
    assert model.value == 4
else:
    raise AssertionError("notification unexpectedly succeeded")
print("rejected candidate: 1; committed quantity: 3; failed notification value: 4")

# Validation is participant-based, not a sweep of every object using the manager.
from yidl_lifecycle.lifecycle import before_commit, field, local_store


@lifecycle
class Eligibility:
    value: int = managed(default=-1)
    note: str = field(default="")
    calls: list[str] = local_store(default_factory=list)

    @validate_commit()
    def valid(self) -> bool:
        self.calls.append("validate")
        return self.value >= 0

    @before_commit()
    def preparing(self) -> None:
        self.calls.append("before")

    @after_commit()
    def published(self) -> None:
        self.calls.append("after")


candidate = Eligibility(transaction_manager=manager)
assert candidate.calls == []  # Construction does not validate this value.
with manager.begin(DEFAULT_TRANSACTION):
    candidate.note = "ordinary edit"
    candidate.value = -1  # Equal assignment does not enlist by itself.
    assert candidate.working.value == -1  # A scalar read does not enlist either.
    assert manager.validate(DEFAULT_TRANSACTION) is None
assert candidate.calls == []
assert candidate.value == -1

with manager.begin(DEFAULT_TRANSACTION):
    candidate.value = 1  # Changed managed replacement enlists.
assert candidate.calls == ["validate", "before", "after"]
print("no-op edit skipped callbacks; enlisted edit ran validator and hooks")
