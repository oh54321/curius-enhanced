from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple, Union, Dict

import pandas as pd

from src.nodes import Link, User, FollowingUser
from src.data_structures import OrderStatisticRedBlackTree
from src.logging import get_logger

logger = get_logger(__name__)


def link_timestamp(link: Link) -> pd.Timestamp:
    ts = pd.to_datetime(
        link.modified_date or link.created_date,
        utc=True,
        errors="coerce",
    )

    if pd.isna(ts):
        return pd.Timestamp("1970-01-01", tz="UTC")

    return ts


class LinkBuffer:
    def __init__(
        self, users: Sequence[Union[FollowingUser, User]], include_users: bool = False
    ) -> None:
        self._user_data = list(users)
        self._user_cache: Dict[int, User] = {}
        self._tree: OrderStatisticRedBlackTree[Tuple[pd.Timestamp, int]] = (
            OrderStatisticRedBlackTree()
        )
        self._links_by_key: Dict[Tuple[pd.Timestamp, int], Link] = {}
        self._links_by_url: Dict[str, Link] = {}
        self._link_users: Dict[str, List[str]] = {}
        self._next_key_id = 0
        self._explored_links: set[str] = set()
        self._user_cutoffs = {
            user.id: pd.Timestamp(user.last_online) for user in self._user_data
        }
        self._max_user_cutoff = max(self._user_cutoffs.values())
        self._max_user_id = max(
            self._user_data, key=lambda user: self._user_cutoffs[user.id]
        ).id
        self._user_pages = {user.id: 0 for user in self._user_data}
        self._first_pages_fetched = False
        self.include_users = include_users

    def _get_user(self, user_data: Union[FollowingUser, User]) -> User:
        if isinstance(user_data, User):
            return user_data
        if user_data.id not in self._user_cache:
            from src.graph import UserGraph

            self._user_cache[user_data.id] = UserGraph.get_user(user_data.user_link)
        return self._user_cache[user_data.id]

    @property
    def users(self) -> List[User]:
        return [self._get_user(user_data) for user_data in self._user_data]

    def _update_user_cutoff(
        self, updated_user_id: int, old_cutoff: pd.Timestamp
    ) -> None:
        new_cutoff = self._user_cutoffs[updated_user_id]

        if updated_user_id == self._max_user_id and new_cutoff < old_cutoff:
            self._max_user_id = max(
                self._user_data, key=lambda user: self._user_cutoffs[user.id]
            ).id
            self._max_user_cutoff = self._user_cutoffs[self._max_user_id]
        elif new_cutoff > self._max_user_cutoff:
            self._max_user_id = updated_user_id
            self._max_user_cutoff = new_cutoff

    def next_user(self) -> User:
        user_data = next(
            user for user in self._user_data if user.id == self._max_user_id
        )
        return self._get_user(user_data)

    def is_exhausted(self) -> bool:
        return self._max_user_cutoff <= self.min_timestamp

    def pop_n(self, n: int) -> List[Link]:
        links = []
        while len(self._tree) > 0 and len(links) < n:
            last_index = len(self._tree) - 1
            key = self._tree.select(last_index)
            self._tree.remove_by_rank(last_index)
            links.append(self._links_by_key.pop(key))

        if self.include_users:
            for link in links:
                self.add_users_to_title(link)
        return links

    def get_next_n(self, n: int) -> List[Link]:
        if len(self.users) == 0:
            return []
        while (
            not self.is_exhausted()
            and self.n_between(self._max_user_cutoff, self.max_timestamp) < n
        ):
            self.process_next()
        return self.pop_n(n)

    def process_next(self) -> None:
        user = self.next_user()
        page = self._user_pages[user.id]
        self._user_pages[user.id] += 1
        links = user.links_page(page)
        old_cutoff = self._user_cutoffs[user.id]
        if len(links) == 0:
            self._user_cutoffs[user.id] = self.min_timestamp
        else:
            self._user_cutoffs[user.id] = links[-1].timestamp
        self._update_user_cutoff(user.id, old_cutoff)
        self.add_links(links, user.name)

    def n_between(
        self, start_timestamp: pd.Timestamp, end_timestamp: pd.Timestamp
    ) -> int:
        if start_timestamp > end_timestamp:
            return 0
        lo_key = (start_timestamp, -1)
        hi_key = (end_timestamp, 2**63 - 1)
        return self._tree.count_range(lo_key, hi_key)

    def add_users_to_title(self, link: Link) -> None:
        users = self._link_users[link.url]
        user_str = ", ".join(users)
        if link._title is not None:
            title = link._title
        else:
            title = link.title
        link.set_title(f"{user_str} | {title}")

    def add_link(self, link: Link, user_name: str) -> None:
        if link.url in self._explored_links:
            if self.include_users:
                self._link_users[link.url].append(user_name)
            return
        key = (link_timestamp(link), self._next_key_id)
        self._next_key_id += 1
        self._tree.insert(key)
        self._links_by_key[key] = link
        if self.include_users:
            self._links_by_url[link.url] = link
            self._link_users[link.url] = [user_name]
        self._explored_links.add(link.url)

    def add_links(self, links: Iterable[Link], user_name: str) -> None:
        for link in links:
            self.add_link(link, user_name)

    @property
    def min_timestamp(self) -> pd.Timestamp:
        return pd.Timestamp("1969-01-01", tz="UTC")

    @property
    def max_timestamp(self) -> pd.Timestamp:
        return pd.Timestamp("2069-01-01", tz="UTC")
