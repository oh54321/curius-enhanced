import abc
from typing import Dict, Optional, List, Literal

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, ListView, ListItem, Label

BACK_KEY = "Back"


class Node(abc.ABC):
    @property
    @abc.abstractmethod
    def type(self) -> Literal["action", "marker", "pane"]:
        raise NotImplementedError

    def is_action(self) -> bool:
        return self.type == "action"

    def is_pane(self) -> bool:
        return self.type == "pane"

    def is_marker(self) -> bool:
        return self.type == "marker"


class ActionNode(Node, abc.ABC):
    @property
    def type(self) -> Literal["action"]:
        return "action"

    @abc.abstractmethod
    def run(self) -> None:
        raise NotImplementedError


class PaneNodeMarker(Node, abc.ABC):
    @property
    def type(self) -> Literal["marker"]:
        return "marker"

    @abc.abstractmethod
    def fetch(self) -> "PaneNode":
        raise NotImplementedError


class PaneNode(Node):
    @property
    def type(self) -> Literal["pane"]:
        return "pane"

    def __init__(self, title: str, block_prev: bool = False) -> None:
        self.title = title
        self._prev: Optional["PaneNode"] = None
        self._children: Dict[str, Node] = {}
        self.block_prev = block_prev

    def _add(self, key: str, node: Node) -> None:
        self._children[key] = node

    def add(self, key: str, node: Node) -> None:
        self._add(key, node)

    def add_action(self, key: str, action: ActionNode) -> None:
        self._add(key, action)

    def add_marker(self, key: str, marker: PaneNodeMarker) -> None:
        self._add(key, marker)

    def add_pane(self, pane_node: "PaneNode", key: Optional[str] = None) -> None:
        if key is None:
            key_ = pane_node.title
        else:
            key_ = key
        self.add(key_, pane_node)

    def get_child(self, key: str) -> Node:
        if key == BACK_KEY:
            if self.has_prev():
                return self._prev
            raise ValueError("Previous node is not set!")
        return self._children[key]

    def add_prev(self, node: "PaneNode") -> None:
        if not self.block_prev:
            self.set_prev(node)

    def get(self, key: str) -> "PaneNode":
        child: Node = self.get_child(key)
        if child.is_marker():
            return child.fetch()
        if child.is_pane():
            return child
        raise ValueError(f"Cannot get pane from node of type '{child.type}'")

    def keys(self) -> List[str]:
        keys = list(self._children.keys())
        if self.has_prev() and BACK_KEY not in keys:
            keys = [BACK_KEY] + keys
        return keys

    def has_prev(self) -> bool:
        return self._prev is not None

    def set_prev(self, node: "PaneNode") -> None:
        self._prev = node

    def clear(self) -> None:
        self._children = {}


class DropdownApp(App):
    def __init__(self, start_node: PaneNode):
        super().__init__()
        self.node = start_node
        self._items: List[str] = self.node.keys()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)

        with Vertical(id="box"):
            self.title_label = Label(self.node.title, classes="pane_title")
            yield self.title_label

            items = [ListItem(Label(key)) for key in self._items]
            self.list_view = ListView(*items)
            yield self.list_view

    def on_mount(self) -> None:
        self.compose()
        self.list_view.focus()

    def _set_list(self, title: str, items: List[str], index: int = 0) -> None:
        self._items = items
        self.title_label.update(title)

        self.list_view.clear()
        self.list_view.extend(ListItem(Label(x)) for x in items)
        self.list_view.call_after_refresh(lambda: self._set_index(index))

    def _set_index(self, index: int) -> None:
        if not self.list_view.children:
            return
        self.list_view.index = min(index, len(self.list_view.children) - 1)
        self.list_view.focus()

    @property
    def items(self) -> List[str]:
        return self._items

    @property
    def current_key(self) -> Optional[str]:
        idx = self.list_view.index
        if idx is None:
            return None
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None

    def index(self) -> int:
        return self.list_view.index

    def set_pane(self, pane: PaneNode) -> Node:
        self.node = pane
        if self.is_mounted:
            self._set_list(self.node.title, self.items)

    def on_list_view_selected(self, _: ListView.Selected) -> None:
        selected_node = self.node.get_child(self.current_key)
        if selected_node.is_action():
            selected_node.run()
            return
        next_pane = self.node.get(self.current_key)
        if not self.current_key == "Back":
            next_pane.add_prev(self.node)
        self.node = next_pane
        self._set_list(self.node.title, self.node.keys())
