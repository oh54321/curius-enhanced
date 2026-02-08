from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")

RED = True
BLACK = False


@dataclass
class _Node(Generic[T]):
    key: Optional[T]
    uid: int
    color: bool
    size: int
    left: "_Node[T]"
    right: "_Node[T]"
    parent: "_Node[T]"


class OrderStatisticRedBlackTree(Generic[T]):
    """Order-statistics red-black tree (augmented with subtree sizes)."""

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._nil = _Node(None, -1, BLACK, 0, None, None, None)  # type: ignore[arg-type]
        self._nil.left = self._nil
        self._nil.right = self._nil
        self._nil.parent = self._nil
        self._root: _Node[T] = self._nil
        self._size = 0
        self._next_uid = 0
        if items is not None:
            for item in items:
                self.insert(item)

    def __len__(self) -> int:
        return self._size

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

    def insert(self, key: T) -> None:
        uid = self._next_uid
        self._next_uid += 1

        parent = self._nil
        current = self._root
        while current is not self._nil:
            parent = current
            if (key, uid) < (current.key, current.uid):  # type: ignore[operator]
                current = current.left
            else:
                current = current.right

        node = _Node(key, uid, RED, 1, self._nil, self._nil, parent)
        if parent is self._nil:
            self._root = node
        elif (key, uid) < (parent.key, parent.uid):  # type: ignore[operator]
            parent.left = node
        else:
            parent.right = node

        self._size += 1
        self._update_sizes_upward(node.parent)  # size updates after insertion path
        self._insert_fixup(node)

    def remove_by_rank(self, k: int) -> None:
        if k < 0 or k >= self._size:
            raise IndexError("rank out of range")
        node = self._select_node(self._root, k)
        self._delete_node(node)

    def select(self, k: int) -> T:
        if k < 0 or k >= self._size:
            raise IndexError("rank out of range")
        node = self._select_node(self._root, k)
        return node.key  # type: ignore[return-value]

    def rank(self, key: T) -> int:
        return self._count_less_than(key)

    def min(self) -> Optional[T]:
        node = self._min_node(self._root)
        return None if node is self._nil else node.key

    def max(self) -> Optional[T]:
        node = self._max_node(self._root)
        return None if node is self._nil else node.key

    def floor(self, key: T) -> Optional[T]:
        current = self._root
        candidate: Optional[T] = None
        while current is not self._nil:
            if key < current.key:  # type: ignore[operator]
                current = current.left
            else:
                candidate = current.key
                current = current.right
        return candidate

    def ceiling(self, key: T) -> Optional[T]:
        current = self._root
        candidate: Optional[T] = None
        while current is not self._nil:
            if key > current.key:  # type: ignore[operator]
                current = current.right
            else:
                candidate = current.key
                current = current.left
        return candidate

    def count_range(self, lo: T, hi: T) -> int:
        if lo > hi:  # type: ignore[operator]
            return 0
        return self._count_less_equal(hi) - self._count_less_than(lo)

    def _select_node(self, node: _Node[T], k: int) -> _Node[T]:
        current = node
        while current is not self._nil:
            left_size = current.left.size
            if k < left_size:
                current = current.left
            elif k == left_size:
                return current
            else:
                k -= left_size + 1
                current = current.right
        raise IndexError("rank out of range")

    def _count_less_than(self, key: T) -> int:
        count = 0
        current = self._root
        while current is not self._nil:
            if key <= current.key:  # type: ignore[operator]
                current = current.left
            else:
                count += current.left.size + 1
                current = current.right
        return count

    def _count_less_equal(self, key: T) -> int:
        count = 0
        current = self._root
        while current is not self._nil:
            if key < current.key:  # type: ignore[operator]
                current = current.left
            else:
                count += current.left.size + 1
                current = current.right
        return count

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

    def _recompute_size(self, node: _Node[T]) -> None:
        # size updated from child sizes (subtree augmentation)
        node.size = node.left.size + node.right.size + 1

    def _update_sizes_upward(self, start: _Node[T]) -> None:
        # size updates after insert/delete affecting ancestors
        current = start
        while current is not self._nil:
            self._recompute_size(current)
            current = current.parent

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
        # size updates after rotation
        self._recompute_size(x)
        self._recompute_size(y)

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
        # size updates after rotation
        self._recompute_size(y)
        self._recompute_size(x)

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
        update_extra_parent: Optional[_Node[T]] = None
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
                update_extra_parent = y.parent
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color
            self._recompute_size(y)  # size updated for transplanted node

        if y_original_color is BLACK:
            self._delete_fixup(x)
        self._size -= 1
        self._update_sizes_upward(x.parent)  # size updates after deletion path
        self._update_sizes_upward(y.parent)
        if update_extra_parent is not None:
            self._update_sizes_upward(update_extra_parent)

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


if __name__ == "__main__":
    tree = OrderStatisticRedBlackTree([5, 1, 3, 3, 9])
    assert list(tree) == [1, 3, 3, 5, 9]
    assert tree.select(2) == 3
    assert tree.rank(3) == 1
    assert tree.count_range(3, 5) == 3
    tree.remove_by_rank(1)
    assert list(tree) == [1, 3, 5, 9]
