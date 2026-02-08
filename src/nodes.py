from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from functools import cached_property

import pandas as pd

from src.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Highlight:
    id: int
    user_id: int
    link_id: int
    highlight: str
    created_date: str
    left_context: str
    right_context: str
    raw_highlight: str
    comment_ids: List[Optional[int]]
    comment: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Highlight":
        return cls(
            id=data["id"],
            user_id=data["userId"],
            link_id=data["linkId"],
            highlight=data["highlight"],
            created_date=data["createdDate"],
            left_context=data.get("leftContext", ""),
            right_context=data.get("rightContext", ""),
            raw_highlight=data.get("rawHighlight", ""),
            comment_ids=list(data.get("comment_ids", data.get("commentIds")) or []),
            comment=data.get("comment"),
        )


@dataclass
class Link:
    id: int
    link: str
    title: str
    favorite: bool
    snippet: Optional[str]
    to_read: Optional[bool]
    created_by: int
    metadata: Optional[Dict[str, Any]]
    created_date: str
    modified_date: str
    last_crawled: Optional[str]
    trails: List[Any]
    comments: List[Any]
    mentions: List[Any]
    topics: List[Any]
    highlights: List[Highlight]
    user_ids: List[int]
    _is_expanded: bool = False
    _title: Optional[str] = None

    def set_title(self, title: str) -> None:
        if self._title is None:
            self._title = title
        self.title = title

    def __lt__(self, other: "Link") -> bool:
        if not isinstance(other, Link):
            raise ValueError("Can only be compared to links!")
        return self.modified_date < other.modified_date

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Link":
        return cls(
            id=data["id"],
            link=data["link"],
            title=data["title"],
            favorite=data["favorite"],
            snippet=data.get("snippet"),
            to_read=data.get("toRead"),
            created_by=data["createdBy"],
            metadata=data.get("metadata"),
            created_date=data["createdDate"],
            modified_date=data["modifiedDate"],
            last_crawled=data.get("lastCrawled"),
            trails=list(data.get("trails", [])),
            comments=list(data.get("comments", [])),
            mentions=list(data.get("mentions", [])),
            topics=list(data.get("topics", [])),
            highlights=[
                Highlight.from_dict(item) for item in data.get("highlights", [])
            ],
            user_ids=list(data.get("userIds", [])),
        )

    @classmethod
    def from_network_dict(cls, data: Dict[str, Any]) -> "Link":
        return cls(
            id=data["id"],
            link=data["link"],
            title=data["title"],
            favorite=data.get("favorite", False),
            snippet=data.get("snippet"),
            to_read=data.get("toRead"),
            created_by=data.get("createdBy", 0),
            metadata=data.get("metadata"),
            created_date=data.get("createdDate") or "",
            modified_date=data.get("modifiedDate") or "",
            last_crawled=data.get("lastCrawled"),
            trails=list(data.get("trails", [])),
            comments=list(data.get("comments", [])),
            mentions=list(data.get("mentions", [])),
            topics=list(data.get("topics", [])),
            highlights=[],
            user_ids=list(data.get("userIds", [])),
        )

    @cached_property
    def network(self) -> "Network":
        from src.graph import UserGraph

        return UserGraph.get_network(self.link)

    @property
    def url(self) -> str:
        return self.link

    @cached_property
    def users(self) -> List["User"]:
        users = self.network.users
        self.set_expanded(True)
        return users

    @property
    def highlights_by_user(self) -> List[Tuple["User", List[Highlight]]]:
        return self.network.highlights_by_user

    def get_highlights(self, user_link: str) -> List[Highlight]:
        from src.graph import UserGraph

        user = UserGraph.get_user(user_link)
        if self.highlights:
            return [
                highlight
                for highlight in self.highlights
                if highlight.user_id == user.id
            ]
        highlights = UserGraph.get_highlights_for_link(self.id)
        return [highlight for highlight in highlights if highlight.user_id == user.id]

    @property
    def connected_users(self) -> List["User"]:
        return self.users

    @property
    def is_expanded(self) -> bool:
        return self._is_expanded

    def set_expanded(self, value: bool) -> None:
        self._is_expanded = value
        from src.graph import UserGraph

        UserGraph.set_link_expanded(self.id, value)

    def expand(self) -> List["User"]:
        logger.debug("Expanding link id=%s url=%s", self.id, self.link)
        return self.users

    @property
    def timestamp(self) -> pd.Timestamp:
        return pd.Timestamp(self.modified_date)


@dataclass
class FollowingUser:
    id: int
    first_name: str
    last_name: str
    user_link: str
    last_online: str


@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    user_link: str
    major: Optional[str]
    interests: Optional[str]
    expertise: Optional[str]
    school: Optional[str]
    github: Optional[str]
    twitter: Optional[str]
    website: Optional[str]
    created_date: str
    modified_date: str
    last_online: str
    last_checked_notifications: str
    views: int
    num_followers: int
    followed: Optional[bool]
    following_me: Optional[bool]
    recent_users: List["User"]
    following_users: List["FollowingUser"]
    _is_expanded: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            id=data["id"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            user_link=data["userLink"],
            major=data.get("major"),
            interests=data.get("interests"),
            expertise=data.get("expertise"),
            school=data.get("school"),
            github=data.get("github"),
            twitter=data.get("twitter"),
            website=data.get("website"),
            created_date=data["createdDate"],
            modified_date=data["modifiedDate"],
            last_online=data["lastOnline"],
            last_checked_notifications=data["lastCheckedNotifications"],
            views=data["views"],
            num_followers=data["numFollowers"],
            followed=data.get("followed"),
            following_me=data.get("followingMe"),
            recent_users=[
                cls.from_marker_dict(item) for item in data.get("recentUsers", [])
            ],
            following_users=[
                FollowingUser(
                    id=item["id"],
                    first_name=item.get("firstName", ""),
                    last_name=item.get("lastName", ""),
                    user_link=item["userLink"],
                    last_online=item.get("lastOnline", ""),
                )
                for item in data.get("followingUsers", [])
            ],
        )

    @property
    def name(self) -> str:
        if len(self.last_name) == 0:
            return self.first_name
        return f"{self.first_name} {self.last_name}"

    @property
    def connected_users(self) -> List["User"]:
        return self.following

    @classmethod
    def from_marker_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            id=data["id"],
            first_name=data["firstName"],
            last_name=data.get("lastName", ""),
            user_link=data["userLink"],
            major=None,
            interests=None,
            expertise=None,
            school=None,
            github=None,
            twitter=None,
            website=None,
            created_date=data.get("createdDate", ""),
            modified_date=data.get("modifiedDate", ""),
            last_online=data.get("lastOnline", ""),
            last_checked_notifications="",
            views=0,
            num_followers=0,
            followed=None,
            following_me=None,
            recent_users=[],
            following_users=[],
        )

    def fetch(self) -> "User":
        from src.graph import UserGraph

        return UserGraph.get_user(self.user_link)

    @cached_property
    def links(self) -> List[Link]:
        from src.graph import UserGraph

        links = UserGraph.get_links(self.id)
        self.set_expanded(True)
        return links

    def links_page(self, page: int) -> List[Link]:
        # TODO: speed up api so we don't have to do this overrwrite
        from src.client import CuriusAPI
        from src.graph import UserGraph

        logger.debug("Fetching links page=%s for user id=%s", page, self.id)
        links_dicts = CuriusAPI.links_page(self.id, page)
        links = [Link.from_dict(item) for item in links_dicts]
        UserGraph.cache_links(self.id, links)
        return links

    @cached_property
    def following(self) -> List["User"]:
        from src.graph import UserGraph

        return [UserGraph.get_user(item.user_link) for item in self.following_users]

    @cached_property
    def is_expanded(self) -> bool:
        return self._is_expanded

    def set_expanded(self, value: bool) -> None:
        self._is_expanded = value
        from src.graph import UserGraph

        UserGraph.set_user_expanded(self.id, value)

    def expand(self) -> List[Link]:
        logger.debug("Expanding user id=%s link=%s", self.id, self.user_link)
        links = self.links
        for following in self.following:
            following.expand()
        return links


@dataclass
class Network:
    link: Link
    user_links: List[str]
    highlights_by_user_id: Dict[int, List[Highlight]]
    user_saved_dates: Dict[int, Optional[str]]
    read_count: int
    user_ids: List[int]

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "Network":
        data = payload.get("networkInfo", payload)
        if not isinstance(data, dict):
            raise ValueError("Network payload missing required link data")
        link_data = None
        if "id" in data and "link" in data:
            link_data = data
        elif isinstance(data.get("link"), dict):
            link_data = data.get("link")
        elif isinstance(payload.get("link"), dict):
            link_data = payload.get("link")
        if link_data is None or "id" not in link_data or "link" not in link_data:
            raise ValueError("Network payload missing required link data")
        users_raw = [item for item in data.get("users", []) if "userLink" in item]
        user_links = [item["userLink"] for item in users_raw]
        user_saved_dates = {
            item["id"]: item.get("savedDate")
            for item in data.get("users", [])
            if "id" in item
        }
        highlights_by_user_id: Dict[int, List[Highlight]] = {}
        for user, highlights in zip(users_raw, data.get("highlights", [])):
            user_id = user["id"]
            highlights_by_user_id[user_id] = [
                Highlight.from_dict(item) for item in highlights
            ]
        return cls(
            link=Link.from_network_dict(link_data),
            user_links=user_links,
            highlights_by_user_id=highlights_by_user_id,
            user_saved_dates=user_saved_dates,
            read_count=data.get("readCount", 0),
            user_ids=list(data.get("userIds", [])),
        )

    @cached_property
    def users(self) -> List["User"]:
        from src.graph import UserGraph

        return [UserGraph.get_user(link) for link in self.user_links]

    @property
    def highlights_by_user(self) -> List[Tuple["User", List[Highlight]]]:
        return [
            (user, self.highlights_by_user_id.get(user.id, [])) for user in self.users
        ]

    def highlights_for(self, user: "User") -> List[Highlight]:
        return self.highlights_by_user_id.get(user.id, [])
