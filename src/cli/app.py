from pathlib import Path
from typing import List, Union

import webbrowser

from src.cli.base import PaneNode, ActionNode, PaneNodeMarker, DropdownApp
from src.buffer import LinkBuffer
from src.nodes import User, Link, FollowingUser
from src.graph import UserGraph


def get_name(first_name: str, last_name: str) -> str:
    if len(last_name) == 0:
        return first_name
    return f"{first_name} {last_name}"


class LinkNode(ActionNode):
    def __init__(self, link: Link):
        self.link = link

    def get_user_name(self, user: User) -> str:
        return get_name(user.first_name, user.last_name)

    @property
    def title(self) -> str:
        return self.link.title

    def run(self) -> None:
        webbrowser.open(self.link.url)


class UserPaneMarker(PaneNodeMarker):
    def __init__(self, user_link: str, first_name: str, last_name: str) -> None:
        self.user_link = user_link
        self.first_name = first_name
        self.last_name = last_name

    @property
    def title(self) -> str:
        return get_name(self.first_name, self.last_name)

    def fetch(self) -> "UserPane":
        user = UserGraph.get_user(self.user_link)
        return UserPane(user)


class UserPane(PaneNode):
    def __init__(self, user: User):
        self.user = user
        super().__init__(self.name)
        self.add_children()

    @property
    def name(self) -> str:
        return get_name(self.user.first_name, self.user.last_name)

    def add_children(self) -> None:
        self.add(
            "Links",
            FeedPaneMarker(f"{self.name}'s Links", [self.user], include_users=False),
        )
        self.add("Following", FollowingPaneMarker(self.user))
        self.add(
            "Feed",
            FeedPaneMarker(
                f"{self.name}'s Feed", self.user.following_users, include_users=True
            ),
        )


class FollowingPane(PaneNode):
    def __init__(self, user: User):
        self.user = user
        super().__init__(f"{self.name}'s Following")
        self.add_children()

    @property
    def name(self) -> str:
        return get_name(self.user.first_name, self.user.last_name)

    def add_children(self) -> None:
        for user in self.user.following_users:
            node = UserPaneMarker(user.user_link, user.first_name, user.last_name)
            self.add(node.title, node)


class FollowingPaneMarker(PaneNodeMarker):
    def __init__(self, user: User):
        self.user = user

    def fetch(self) -> FollowingPane:
        return FollowingPane(self.user)


class FeedPane(PaneNode):
    def __init__(
        self,
        title: str,
        users: List[Union[FollowingUser, User]],
        page_size: int = 30,
        include_users: bool = True,
    ):
        self.header = title
        super().__init__(f"{title}, Page 1")
        self.buffer = LinkBuffer(users, include_users)
        self._page_links: List[List[LinkNode]] = []
        self._current_page: int = 0
        self.page_size = page_size
        self.add_page()
        self.add_children()

    def is_last_page(self) -> bool:
        if not self.buffer.is_exhausted():
            return False
        return self._current_page == len(self._page_links) - 1

    def add_page(self) -> None:
        if self.buffer.is_exhausted():
            return
        links = self.buffer.get_next_n(self.page_size)
        link_panes = [LinkNode(link) for link in links]
        if len(links) > 0 or len(self._page_links) == 0:
            self._page_links.append(link_panes)

    def page(self) -> List[LinkNode]:
        return self._page_links[self._current_page]

    def add_children(self) -> None:
        self.clear()
        for link in self.page():
            self.add(link.title, link)
        if self._current_page != 0:
            self.add("Prev", self)
        if not self.is_last_page():
            self.add("Next", self)

    def set_title(self) -> None:
        self.title = f"{self.header}, Page {self._current_page + 1}"

    def prev(self) -> None:
        self._current_page = max((self._current_page - 1), 0)
        self.add_children()
        self.set_title()

    def add_prev(self, node: PaneNode) -> None:
        if self.has_prev():
            return
        super().add_prev(node)

    def next(self) -> None:
        self._current_page = self._current_page + 1
        if self._current_page >= len(self._page_links):
            self.add_page()
        if self._current_page >= len(self._page_links):
            self._current_page = len(self._page_links) - 1
        self.add_children()
        self.set_title()

    def get(self, key: str) -> PaneNode:
        node = super().get(key)
        if key == "Prev":
            self.prev()
        if key == "Next":
            self.next()
        return node


class FeedPaneMarker(PaneNodeMarker):
    def __init__(
        self,
        title: str,
        users: List[Union[FollowingUser, User]],
        page_size: int = 30,
        include_users: bool = False,
    ):
        self.title = title
        self.users = users
        self.page_size = page_size
        self.include_users = include_users

    def fetch(self) -> FeedPane:
        return FeedPane(self.title, self.users, self.page_size, self.include_users)


class CuriusCLI(DropdownApp):
    CSS_PATH = str(Path(__file__).resolve().parent / "template.css")

    def __init__(self, start_user_link: str) -> None:
        start_user = UserGraph.get_user(start_user_link)
        super().__init__(UserPane(start_user))
