from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from src.client import CuriusAPI
from src.logging import get_logger
from src.nodes import Highlight, Link, Network, User

logger = get_logger(__name__)


@dataclass
class _GraphStore:
    users_by_id: Dict[int, User] = field(default_factory=dict)
    users_by_link: Dict[str, User] = field(default_factory=dict)
    links_by_id: Dict[int, Link] = field(default_factory=dict)
    links_by_url: Dict[str, Link] = field(default_factory=dict)
    links_by_user_id: Dict[int, List[Link]] = field(default_factory=dict)
    networks_by_url: Dict[str, Network] = field(default_factory=dict)
    networks_by_link_id: Dict[int, Network] = field(default_factory=dict)
    highlights_by_id: Dict[int, Highlight] = field(default_factory=dict)
    highlights_by_link_id: Dict[int, List[Highlight]] = field(default_factory=dict)


class _UserGraph:
    def __init__(self) -> None:
        self._store = _GraphStore()

    def clear(self) -> None:
        logger.info("Clearing graph cache")
        for user in self._store.users_by_id.values():
            user.set_expanded(False)
        for link in self._store.links_by_id.values():
            link.set_expanded(False)
        self._store = _GraphStore()

    def _cache_user(self, user: User) -> None:
        existing = self._store.users_by_id.get(user.id)
        if existing is not None and existing.is_expanded:
            user.set_expanded(True)
        self._store.users_by_id[user.id] = user
        self._store.users_by_link[user.user_link] = user

    def _cache_link(self, link: Link) -> None:
        existing = self._store.links_by_id.get(link.id)
        if existing is not None and existing.is_expanded:
            link.set_expanded(True)
        self._store.links_by_id[link.id] = link
        self._store.links_by_url[link.link] = link
        if link.highlights:
            self._store.highlights_by_link_id[link.id] = link.highlights
            for highlight in link.highlights:
                self._store.highlights_by_id[highlight.id] = highlight

    def _cache_links_for_user(self, user_id: int, links: List[Link]) -> None:
        self._store.links_by_user_id[user_id] = links
        for link in links:
            self._cache_link(link)

    def cache_links(self, user_id: int, links: List[Link]) -> None:
        self._cache_links_for_user(user_id, links)

    def _cache_network(self, network: Network) -> None:
        self._store.networks_by_url[network.link.link] = network
        self._store.networks_by_link_id[network.link.id] = network
        self._cache_link(network.link)
        highlights = [
            item
            for user_highlights in (network.highlights_by_user_id or {}).values()
            for item in user_highlights
        ]
        if highlights:
            self._store.highlights_by_link_id[network.link.id] = highlights
            for highlight in highlights:
                self._store.highlights_by_id[highlight.id] = highlight

    def _normalize_url(self, url: str) -> str:
        url = url.strip()
        if not url:
            return url
        parsed = urlparse(url)
        if not parsed.scheme and parsed.path:
            parsed = urlparse(f"https://{url}")
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return urlunparse((scheme, netloc, path, "", "", ""))

    def _candidate_urls(self, url: str) -> List[str]:
        normalized = self._normalize_url(url)
        candidates: List[str] = [url, normalized]

        if normalized.startswith("http://"):
            candidates.append("https://" + normalized[len("http://") :])
        if normalized.endswith("/"):
            candidates.append(normalized.rstrip("/"))
        if normalized.endswith(".pdf"):
            candidates.append(normalized[: -len(".pdf")])

        if "arxiv.org/pdf/" in normalized:
            arxiv_abs = normalized.replace("arxiv.org/pdf/", "arxiv.org/abs/")
            candidates.append(arxiv_abs)
            if arxiv_abs.endswith(".pdf"):
                candidates.append(arxiv_abs[: -len(".pdf")])
        if "arxiv.org/abs/" in normalized and normalized.endswith(".pdf"):
            candidates.append(normalized[: -len(".pdf")])

        # Preserve order but remove duplicates/empties.
        seen = set()
        unique: List[str] = []
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            unique.append(candidate)
        return unique

    def set_user_expanded(self, user_id: int, value: bool) -> None:
        user = self._store.users_by_id.get(user_id)
        if user is not None:
            user._is_expanded = value

    def set_link_expanded(self, link_id: int, value: bool) -> None:
        link = self._store.links_by_id.get(link_id)
        if link is not None:
            link._is_expanded = value

    def get_user(self, user_link: str, *, use_cache: bool = True) -> User:
        if use_cache:
            cached = self._store.users_by_link.get(user_link)
            if cached is not None:
                logger.debug("User cache hit for %s", user_link)
                return cached
        logger.debug("User cache miss for %s", user_link)
        user_dict = CuriusAPI.get_user_dict(user_link)
        user = User.from_dict(user_dict)
        if use_cache:
            self._cache_user(user)
        return user

    def get_user_by_id(self, user_id: int, *, use_cache: bool = True) -> Optional[User]:
        if use_cache:
            cached = self._store.users_by_id.get(user_id)
            if cached is not None:
                return cached
        return None

    def get_links(self, user_id: int, *, use_cache: bool = True) -> List[Link]:
        if use_cache:
            cached = self._store.links_by_user_id.get(user_id)
            if cached is not None:
                logger.debug("Links cache hit for user_id=%s", user_id)
                return cached
        logger.debug("Links cache miss for user_id=%s", user_id)
        links_dicts = CuriusAPI.get_links_dicts(user_id)
        links = [Link.from_dict(item) for item in links_dicts]
        if use_cache:
            self._cache_links_for_user(user_id, links)
        return links

    def get_link_by_url(self, url: str, *, use_cache: bool = True) -> Optional[Link]:
        if use_cache:
            cached = self._store.links_by_url.get(url)
            if cached is not None:
                logger.debug("Link cache hit for url=%s", url)
                return cached
        logger.debug("Link cache miss for url=%s", url)
        network = self.get_network(url, use_cache=use_cache)
        return network.link if network else None

    def get_network(self, url: str, *, use_cache: bool = True) -> Network:
        candidates = self._candidate_urls(url)
        if use_cache:
            for candidate in candidates:
                cached = self._store.networks_by_url.get(candidate)
                if cached is not None:
                    logger.debug("Network cache hit for url=%s", candidate)
                    return cached

        last_error: Optional[Exception] = None
        for candidate in candidates:
            logger.debug("Network cache miss for url=%s", candidate)
            payload = CuriusAPI.get_network_payload(candidate)
            try:
                network = Network.from_payload(payload)
            except ValueError as exc:
                last_error = exc
                logger.error("Invalid network payload for url=%s: %s", candidate, exc)
                continue
            if network is None:
                last_error = ValueError(
                    f"Network payload returned None for url={candidate}"
                )
                logger.error("Network payload returned None for url=%s", candidate)
                continue
            if use_cache:
                self._cache_network(network)
                for cache_url in candidates:
                    self._store.networks_by_url[cache_url] = network
            return network

        if last_error is not None:
            raise last_error
        raise ValueError(f"Network payload missing required link data for url={url}")

    def get_highlights_for_link(
        self, link_id: int, *, use_cache: bool = True
    ) -> List[Highlight]:
        if use_cache:
            cached = self._store.highlights_by_link_id.get(link_id)
            if cached is not None:
                logger.debug("Highlights cache hit for link_id=%s", link_id)
                return cached
        logger.debug("Highlights cache miss for link_id=%s", link_id)
        link = self._store.links_by_id.get(link_id) if use_cache else None
        if link is not None and link.highlights:
            self._store.highlights_by_link_id[link_id] = link.highlights
            for highlight in link.highlights:
                self._store.highlights_by_id[highlight.id] = highlight
            return link.highlights
        return []

    def cached_users(self) -> List[User]:
        return list(self._store.users_by_id.values())

    def cached_links(self) -> List[Link]:
        return list(self._store.links_by_id.values())

    def expand_all(self, start_user_link: str) -> None:
        self._dfs(start_user_link)

    def _dfs(self, start_user_link: str) -> None:
        visited_user_links = set()
        visited_link_ids = set()
        stack = [start_user_link]

        while stack:
            user_link = stack.pop()
            if user_link in visited_user_links:
                continue
            user = self.get_user(user_link)
            visited_user_links.add(user_link)

            for following in user.following:
                self._cache_user(following)
                following.expand()
                if following.user_link not in visited_user_links:
                    stack.append(following.user_link)

            links = user.expand()
            for link in links:
                if link.id in visited_link_ids:
                    continue
                visited_link_ids.add(link.id)
                link.expand()
                for linked_user in link.users:
                    if linked_user.user_link not in visited_user_links:
                        stack.append(linked_user.user_link)


UserGraph = _UserGraph()
