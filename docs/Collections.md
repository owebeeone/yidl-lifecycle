# Edit collections without changing committed values

Use this when an edit appends, removes or rearranges items. Read
[fields and views](Concepts.md) first.

A mutable list stored directly in a managed field can be changed in place
without going through assignment. The transaction cannot undo arbitrary mutation
of a shared object. Declare a committed representation and an editable working
representation instead:

```python
from yidl_lifecycle.lifecycle import lifecycle, managed
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION, TransactionManager


@lifecycle
class Playlist:
    tracks: tuple[str, ...] = managed(default=(), thaw=list, freeze=tuple)


manager = TransactionManager()
playlist = Playlist(transaction_manager=manager)

with manager.begin(DEFAULT_TRANSACTION):
    playlist.working.tracks.append("first")
    assert playlist.current.tracks == ()
    assert playlist.working.tracks == ["first"]

assert playlist.tracks == ("first",)

try:
    with manager.begin(DEFAULT_TRANSACTION):
        playlist.working.tracks.append("discarded")
        raise ValueError("cancel")
except ValueError:
    pass

assert playlist.tracks == ("first",)
print(playlist.tracks)
```

It prints `('first',)`. On working access during the transaction, `thaw`
creates a list from the committed tuple. Commit uses `freeze` to create the
next committed tuple. Rollback discards the working representation.

Use `playlist.working.tracks` to request editable storage. An ordinary
`playlist.tracks` read does not initiate thawing. Outside a healthy active
transaction, working access returns the committed representation.

## Keep conversions honest

`list` and `tuple` only copy the outer collection. If a tuple contains mutable
dictionaries, both representations still refer to those dictionaries. Choose
immutable elements or conversions that isolate the mutable data your application
will change. The annotations do not perform that conversion for you.

Do not retain a mutable working reference and reuse it after commit or rollback.
Its edit lifetime has ended. Start the next transaction and obtain its working
collection again.

The [executable example](../examples/collections.py) covers both outcomes.
Next, [coordinate edits to related objects](Transactions.md).
