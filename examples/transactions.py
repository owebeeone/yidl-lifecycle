from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Stock:
    quantity: int = managed(default=0)


manager = TransactionManager()
source = Stock(quantity=10, transaction_manager=manager)
destination = Stock(quantity=2, transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    source.quantity -= 3
    destination.quantity += 3
    assert (source.current.quantity, destination.current.quantity) == (10, 2)

print(source.quantity, destination.quantity)

transaction = manager.begin(DEFAULT_TRANSACTION)
source.quantity = 6
manager.rollback(DEFAULT_TRANSACTION)
assert source.quantity == 7

transaction = manager.begin(DEFAULT_TRANSACTION)
source.quantity = 6
manager.commit(DEFAULT_TRANSACTION)
assert source.quantity == 6

with manager.begin(DEFAULT_TRANSACTION):
    source.quantity = 4
    with manager.begin(DEFAULT_TRANSACTION):
        destination.quantity = 7
    assert source.current.quantity == 6  # Inner exit has not published.
assert (source.quantity, destination.quantity) == (4, 7)

try:
    with manager.begin(DEFAULT_TRANSACTION):
        source.quantity = 0
        with manager.begin(DEFAULT_TRANSACTION):
            destination.quantity = 0
            raise ValueError('abort joined edit')
except ValueError:
    pass
assert (source.quantity, destination.quantity) == (4, 7)
assert manager.active_transaction is None
from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager

AUDIT = "audit"


@lifecycle
class Record:
    value: int = managed(default=0)
    audit_count: int = managed(AUDIT, default=0)


manager = TransactionManager(tx_keys=(AUDIT,))
record = Record(transaction_manager=manager)
with manager.begin(AUDIT):
    record.audit_count = 1
assert record.value == 0
assert record.audit_count == 1

print('shared edits, joined rollback and custom key passed')
