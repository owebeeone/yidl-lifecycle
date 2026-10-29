from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Settings:
    volume: int = managed(default=5)
    brightness: int = managed(default=50)


manager = TransactionManager()
settings = Settings(transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    settings.volume = 8
    settings.brightness = 70
    print("during:", settings.current.volume, settings.working.volume)

print("committed:", settings.volume, settings.brightness)

try:
    with manager.begin(DEFAULT_TRANSACTION):
        settings.volume = 2
        settings.brightness = 10
        raise ValueError("cancel this edit")
except ValueError:
    pass

print("after cancel:", settings.volume, settings.brightness)

try:
    settings.volume = 3
except RuntimeError:
    print("start a transaction before editing")

transaction = manager.begin(DEFAULT_TRANSACTION)
settings.volume = 1
manager.rollback(DEFAULT_TRANSACTION)
assert settings.volume == 8
transaction = manager.begin(DEFAULT_TRANSACTION)
settings.volume = 9
manager.commit(DEFAULT_TRANSACTION)
assert settings.volume == 9
