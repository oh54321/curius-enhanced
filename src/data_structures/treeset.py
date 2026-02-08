from __future__ import annotations

from typing import Generic, Iterable, Iterator, Optional, TypeVar

from src.data_structures.red_black_tree import RedBlackTree

T = TypeVar("T")


class TreeSet(Generic[T]):
    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._tree = RedBlackTree[T](items)

    def __len__(self) -> int:
        return len(self._tree)

    def __contains__(self, item: T) -> bool:
        return item in self._tree

    def __iter__(self) -> Iterator[T]:
        return iter(self._tree)

    def __repr__(self) -> str:
        return f"TreeSet({list(self._tree)})"

    def add(self, item: T) -> bool:
        return self._tree.insert(item)

    def discard(self, item: T) -> bool:
        return self._tree.discard(item)

    def remove(self, item: T) -> None:
        self._tree.remove(item)

    def clear(self) -> None:
        self._tree.clear()

    def first(self) -> Optional[T]:
        return self._tree.min()

    def last(self) -> Optional[T]:
        return self._tree.max()
