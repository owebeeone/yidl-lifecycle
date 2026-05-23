"""Binding dict/list with lazy COW frozen views (default for YIDL).

For explicit per-slot ``inc_ref``/``dec_ref`` and frozen snapshots as ``BindingBase``
(e.g. lifecycle parity or alternate Python VMs), use ``yidl_lifecycle.bindings_refcount``
(see ``tests/test_bindings_refcount.py``).
"""

from __future__ import annotations

from abc import ABC
from collections import UserDict, UserList
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Union


@dataclass(eq=False, slots=True)
class BindingBase(ABC):
    _accepted: bool = field(default=False, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def is_accepted(self) -> bool:
        return getattr(self, "_accepted", False)

    @property
    def is_closed(self) -> bool:
        # Defensive fallback in case __init__ fails before setting _closed
        return getattr(self, "_closed", True)

    def accepted(self) -> None:
        if self.is_closed:
            raise RuntimeError("cannot accept a closed binding")
        self._accepted = True

    def _close(self) -> None:
        """Override in subclasses to perform actual cleanup logic."""
        pass

    def __del__(self) -> None:
        """
        Intrinsic Teardown: Guaranteed to fire the microsecond the 
        C-level reference count drops to 0.
        """
        if not self.is_closed:
            self._closed = True
            self._close()


@dataclass(eq=False, slots=True)
class FrozenBindingDict(Mapping[Any, BindingBase]):
    """
    Immutable snapshot of a BindingDict's entries. 
    Python handles the lifetimes of the underlying elements automatically.
    """
    _data: dict[Any, BindingBase] = field(repr=False)

    def __getitem__(self, key: Any) -> BindingBase:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: Any, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()


@dataclass(eq=False, slots=True)
class FrozenBindingList:
    """
    Immutable snapshot of a BindingList's elements. 
    Retained by lazy COW lists until they copy-on-write or are released.
    """
    _data: list[BindingBase] = field(repr=False)

    def __getitem__(self, i: Union[int, slice]) -> Any:
        return self._data[i]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, item: object) -> bool:
        return item in self._data


class BindingDict(UserDict):
    """
    A dictionary variant utilizing intrinsic ref counting for BindingBase values.

    ``frozen=`` constructs a lazy copy-on-write view: reads proxy to the frozen
    snapshot until the first mutating operation, which copies entries (leveraging 
    C-level ref counting) and releases the frozen container ref.
    """

    __slots__ = ("_cow_parent",)

    def __init__(self, dict=None, /, *, frozen: FrozenBindingDict | None = None, **kwargs):
        self._cow_parent: FrozenBindingDict | None = None
        self.data: dict[Any, BindingBase] = {}
        
        if frozen is not None:
            if dict is not None or kwargs:
                raise TypeError("BindingDict: cannot combine frozen= with initial mapping arguments")
            self._cow_parent = frozen
            return
            
        if dict is not None:
            if isinstance(dict, BindingDict):
                self.update(dict)
            elif isinstance(dict, BindingList):
                for i, v in enumerate(dict):
                    self[i] = v
            elif hasattr(dict, "keys"):
                for k in dict:
                    self.data[k] = dict[k]
            else:
                for k, v in dict:
                    self.data[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self.data[k] = v

    @classmethod
    def cow_from_frozen(cls, frozen: FrozenBindingDict) -> BindingDict:
        return cls(frozen=frozen)

    def _read_map(self) -> Mapping[Any, BindingBase]:
        p = self._cow_parent
        return p._data if p is not None else self.data

    def _materialize_cow_if_needed(self) -> None:
        parent = self._cow_parent
        if parent is None:
            return
            
        # Native Python handles incrementing C-level ref counts instantly
        self.data.update(parent._data)
        self._cow_parent = None

    def _detach_cow_without_copy(self) -> None:
        self._cow_parent = None

    def freeze(self) -> FrozenBindingDict:
        self._materialize_cow_if_needed()
        snapshot = self.data
        self.data = {}
        return FrozenBindingDict(snapshot)

    # --- Read Methods ---
    def __getitem__(self, key: Any) -> BindingBase:
        return self._read_map()[key]

    def __contains__(self, key: object) -> bool:
        return key in self._read_map()

    def __iter__(self):
        return iter(self._read_map())

    def __len__(self) -> int:
        return len(self._read_map())

    def get(self, key: Any, default: Any = None) -> Any:
        return self._read_map().get(key, default)

    def keys(self):
        return self._read_map().keys()

    def values(self):
        return self._read_map().values()

    def items(self):
        return self._read_map().items()

    # --- Write Methods ---
    # Intercept to materialize COW, then defer entirely to native UserDict behavior
    
    def __setitem__(self, key: Any, value: BindingBase) -> None:
        self._materialize_cow_if_needed()
        super().__setitem__(key, value)

    def __delitem__(self, key: Any) -> None:
        self._materialize_cow_if_needed()
        super().__delitem__(key)

    def pop(self, key: Any, *args) -> Any:
        self._materialize_cow_if_needed()
        return super().pop(key, *args)

    def popitem(self) -> tuple[Any, Any]:
        self._materialize_cow_if_needed()
        return super().popitem()

    def clear(self) -> None:
        self._detach_cow_without_copy()
        super().clear()

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if self._cow_parent is not None and key in self._cow_parent._data:
            return self._cow_parent._data[key]
        self._materialize_cow_if_needed()
        return super().setdefault(key, default)

    def update(self, *args, **kwargs) -> None:
        self._materialize_cow_if_needed()
        if args:
            other = args[0]
            if isinstance(other, BindingList):
                for i, v in enumerate(other):
                    self[i] = v
            elif hasattr(other, "keys"):
                for k in other:
                    self[k] = other[k]
            else:
                for k, v in other:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def copy(self) -> BindingDict:
        self._materialize_cow_if_needed()
        return type(self)(self.data)

    def __copy__(self) -> BindingDict:
        return self.copy()

    def __ior__(self, other):
        self._materialize_cow_if_needed()
        return super().__ior__(other)


class BindingList(UserList):
    """
    A list variant utilizing intrinsic ref counting for BindingBase values.
    """

    __slots__ = ("_cow_parent",)

    def __init__(self, initlist: Iterable[BindingBase] | None = None, *, frozen: FrozenBindingList | None = None):
        self._cow_parent: FrozenBindingList | None = None
        self.data: list[BindingBase] = []
        
        if frozen is not None:
            if initlist is not None:
                raise TypeError("BindingList: cannot combine frozen= with initlist")
            self._cow_parent = frozen
            return
            
        if initlist is not None:
            if isinstance(initlist, BindingList):
                self.extend(initlist)
            elif isinstance(initlist, BindingDict):
                self.extend(initlist.values())
            else:
                self.data.extend(initlist)

    @classmethod
    def cow_from_frozen(cls, frozen: FrozenBindingList) -> BindingList:
        return cls(frozen=frozen)

    def _read_seq(self) -> list[BindingBase]:
        p = self._cow_parent
        return p._data if p is not None else self.data

    def _materialize_cow_if_needed(self) -> None:
        parent = self._cow_parent
        if parent is None:
            return
        self.data.extend(parent._data)
        self._cow_parent = None

    def _detach_cow_without_copy(self) -> None:
        self._cow_parent = None

    def freeze(self) -> FrozenBindingList:
        self._materialize_cow_if_needed()
        snapshot = self.data
        self.data = []
        return FrozenBindingList(snapshot)

    # --- Read Methods ---
    def __getitem__(self, i: Union[int, slice]):
        seq = self._read_seq()
        if isinstance(i, slice):
            return type(self)(seq[i])
        return seq[i]

    def __len__(self) -> int:
        return len(self._read_seq())

    def __contains__(self, item: object) -> bool:
        return item in self._read_seq()

    def count(self, item: BindingBase) -> int:
        return self._read_seq().count(item)

    def index(self, item: BindingBase, *args: Any) -> int:
        return self._read_seq().index(item, *args)

    def __eq__(self, other: object) -> bool:
        oc = other.data if isinstance(other, UserList) else other
        return self._read_seq() == oc

    def __lt__(self, other: object) -> bool:
        oc = other.data if isinstance(other, UserList) else other
        return self._read_seq() < oc

    def __le__(self, other: object) -> bool:
        oc = other.data if isinstance(other, UserList) else other
        return self._read_seq() <= oc

    def __gt__(self, other: object) -> bool:
        oc = other.data if isinstance(other, UserList) else other
        return self._read_seq() > oc

    def __ge__(self, other: object) -> bool:
        oc = other.data if isinstance(other, UserList) else other
        return self._read_seq() >= oc

    def __add__(self, other: Iterable[BindingBase]):
        base = self._read_seq()
        if isinstance(other, UserList):
            return type(self)(base + other.data)
        if isinstance(other, list):
            return type(self)(base + other)
        return type(self)(base + list(other))

    def __radd__(self, other: Iterable[BindingBase]):
        base = self._read_seq()
        if isinstance(other, UserList):
            return type(self)(other.data + base)
        if isinstance(other, list):
            return type(self)(other + base)
        return type(self)(list(other) + base)

    def __mul__(self, n: int):
        return type(self)(self._read_seq() * n)

    __rmul__ = __mul__

    def __repr__(self) -> str:
        return repr(self._read_seq())

    # --- Write Methods ---
    def __setitem__(self, i: Union[int, slice], item: Union[BindingBase, Iterable[BindingBase]]) -> None:
        self._materialize_cow_if_needed()
        super().__setitem__(i, item)

    def __delitem__(self, i: Union[int, slice]) -> None:
        self._materialize_cow_if_needed()
        super().__delitem__(i)

    def append(self, item: BindingBase) -> None:
        self._materialize_cow_if_needed()
        super().append(item)

    def insert(self, i: int, item: BindingBase) -> None:
        self._materialize_cow_if_needed()
        super().insert(i, item)

    def extend(self, other: Iterable[BindingBase]) -> None:
        self._materialize_cow_if_needed()
        if isinstance(other, BindingDict):
            super().extend(other.values())
        else:
            super().extend(other)

    def pop(self, i: int = -1) -> BindingBase:
        self._materialize_cow_if_needed()
        return super().pop(i)

    def clear(self) -> None:
        self._detach_cow_without_copy()
        super().clear()

    def remove(self, item: BindingBase) -> None:
        self._materialize_cow_if_needed()
        super().remove(item)

    def __iadd__(self, other: Iterable[BindingBase]):
        self._materialize_cow_if_needed()
        return super().__iadd__(other)

    def __imul__(self, n: int):
        self._materialize_cow_if_needed()
        return super().__imul__(n)

    def reverse(self) -> None:
        self._materialize_cow_if_needed()
        super().reverse()

    def sort(self, /, *args: Any, **kwds: Any) -> None:
        self._materialize_cow_if_needed()
        super().sort(*args, **kwds)

    def copy(self) -> BindingList:
        self._materialize_cow_if_needed()
        return type(self)(self.data)

    def __copy__(self) -> BindingList:
        return self.copy()