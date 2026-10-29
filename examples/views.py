from yidl_lifecycle.lifecycle import field, lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Counter:
    count: int = managed(default=0)
    last_attempt: str = field(default="none")


manager = TransactionManager()
counter = Counter(transaction_manager=manager)
saved_view = counter.current

try:
    with manager.begin(DEFAULT_TRANSACTION):
        counter.count = 4
        counter.last_attempt = "changed count"
        raise ValueError("cancel")
except ValueError:
    pass

print(counter.count, counter.last_attempt)
with manager.begin(DEFAULT_TRANSACTION):
    counter.count = 7
print(saved_view.count)
