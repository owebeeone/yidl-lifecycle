"""Observe accepted ownership without assuming rollback reverses resource effects."""
from yidl_lifecycle.bindings import BindingBase
from yidl_lifecycle.lifecycle import lifecycle, owned
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


class Resource(BindingBase):
    pass


@lifecycle
class Holder:
    resource: object = owned(default=None)


manager = TransactionManager()
holder = Holder(transaction_manager=manager)
resource = Resource()
with manager.begin(DEFAULT_TRANSACTION):
    holder.resource = resource
    assert holder.current.resource is None
assert holder.resource is resource
assert resource.is_accepted

replacement = Resource()
try:
    with manager.begin(DEFAULT_TRANSACTION):
        holder.resource = replacement
        raise ValueError("cancel before commit preparation")
except ValueError:
    pass
assert holder.resource is resource
assert not replacement.is_accepted
print("committed resource accepted; cancelled replacement not accepted")
