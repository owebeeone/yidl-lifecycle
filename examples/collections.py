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
