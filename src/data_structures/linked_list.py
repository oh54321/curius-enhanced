from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")


@dataclass
class LinkedListNode(Generic[T]):
    value: T
    prev: Optional["LinkedListNode[T]"] = None
    next: Optional["LinkedListNode[T]"] = None


class LinkedList(Generic[T]):
    def __init__(self, values: Iterable[T] = ()) -> None:
        self.head: Optional[LinkedListNode[T]] = None
        self.tail: Optional[LinkedListNode[T]] = None
        self._size = 0
        self.extend(values)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        node = self.head
        while node is not None:
            yield node.value
            node = node.next

    def append(self, value: T) -> LinkedListNode[T]:
        node = LinkedListNode(value=value)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self._size += 1
        return node

    def extend(self, values: Iterable[T]) -> None:
        for value in values:
            self.append(value)

    def clear(self) -> None:
        self.head = None
        self.tail = None
        self._size = 0

    def remove(self, node: LinkedListNode[T]) -> T:
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        self._size -= 1
        node.prev = None
        node.next = None
        return node.value
