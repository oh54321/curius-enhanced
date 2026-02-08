from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")

RED = True
BLACK = False


@dataclass
class _Node(Generic[T]):
    key: Optional[T]
    color: bool
    left: "_Node[T]"
    right: "_Node[T]"
    parent: "_Node[T]"


class RedBlackTree(Generic[T]):
    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._nil = _Node(None, BLACK, None, None, None)  # type: ignore[arg-type]
        self._nil.left = self._nil
        self._nil.right = self._nil
        self._nil.parent = self._nil
        self._root: _Node[T] = self._nil
        self._size = 0
        if items is not None:
            for item in items:
                self.insert(item)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: T) -> bool:
        return self._find_node(key) is not self._nil

    def __iter__(self) -> Iterator[T]:
        return self.inorder()

    def inorder(self) -> Iterator[T]:
        yield from self._inorder_nodes(self._root)

    def _inorder_nodes(self, node: _Node[T]) -> Generator[T, None, None]:
        if node is self._nil:
            return
        yield from self._inorder_nodes(node.left)
        yield node.key  # type: ignore[misc]
        yield from self._inorder_nodes(node.right)

    def min(self) -> Optional[T]:
        node = self._min_node(self._root)
        return None if node is self._nil else node.key

    def max(self) -> Optional[T]:
        node = self._max_node(self._root)
        return None if node is self._nil else node.key

    def insert(self, key: T) -> bool:
        parent = self._nil
        current = self._root
        while current is not self._nil:
            parent = current
            if key == current.key:
                return False
            if key < current.key:  # type: ignore[operator]
                current = current.left
            else:
                current = current.right

        node = _Node(key, RED, self._nil, self._nil, parent)
        if parent is self._nil:
            self._root = node
        elif key < parent.key:  # type: ignore[operator]
            parent.left = node
        else:
            parent.right = node

        self._size += 1
        self._insert_fixup(node)
        return True

    def discard(self, key: T) -> bool:
        node = self._find_node(key)
        if node is self._nil:
            return False
        self._delete_node(node)
        return True

    def remove(self, key: T) -> None:
        if not self.discard(key):
            raise KeyError(key)

    def clear(self) -> None:
        self._root = self._nil
        self._size = 0

    def _find_node(self, key: T) -> _Node[T]:
        current = self._root
        while current is not self._nil:
            if key == current.key:
                return current
            if key < current.key:  # type: ignore[operator]
                current = current.left
            else:
                current = current.right
        return self._nil

    def _min_node(self, node: _Node[T]) -> _Node[T]:
        current = node
        while current is not self._nil and current.left is not self._nil:
            current = current.left
        return current

    def _max_node(self, node: _Node[T]) -> _Node[T]:
        current = node
        while current is not self._nil and current.right is not self._nil:
            current = current.right
        return current

    def _rotate_left(self, x: _Node[T]) -> None:
        y = x.right
        x.right = y.left
        if y.left is not self._nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is self._nil:
            self._root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _rotate_right(self, y: _Node[T]) -> None:
        x = y.left
        y.left = x.right
        if x.right is not self._nil:
            x.right.parent = y
        x.parent = y.parent
        if y.parent is self._nil:
            self._root = x
        elif y is y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x

    def _insert_fixup(self, z: _Node[T]) -> None:
        while z.parent.color is RED:
            if z.parent is z.parent.parent.left:
                y = z.parent.parent.right
                if y.color is RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._rotate_left(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._rotate_right(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y.color is RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._rotate_right(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._rotate_left(z.parent.parent)
        self._root.color = BLACK

    def _transplant(self, u: _Node[T], v: _Node[T]) -> None:
        if u.parent is self._nil:
            self._root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _delete_node(self, z: _Node[T]) -> None:
        y = z
        y_original_color = y.color
        if z.left is self._nil:
            x = z.right
            self._transplant(z, z.right)
        elif z.right is self._nil:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._min_node(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent is z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        if y_original_color is BLACK:
            self._delete_fixup(x)
        self._size -= 1

    def _delete_fixup(self, x: _Node[T]) -> None:
        while x is not self._root and x.color is BLACK:
            if x is x.parent.left:
                w = x.parent.right
                if w.color is RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._rotate_left(x.parent)
                    w = x.parent.right
                if w.left.color is BLACK and w.right.color is BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.right.color is BLACK:
                        w.left.color = BLACK
                        w.color = RED
                        self._rotate_right(w)
                        w = x.parent.right
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._rotate_left(x.parent)
                    x = self._root
            else:
                w = x.parent.left
                if w.color is RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._rotate_right(x.parent)
                    w = x.parent.left
                if w.right.color is BLACK and w.left.color is BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.left.color is BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._rotate_left(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._rotate_right(x.parent)
                    x = self._root
        x.color = BLACK
