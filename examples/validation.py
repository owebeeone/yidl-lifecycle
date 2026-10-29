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
