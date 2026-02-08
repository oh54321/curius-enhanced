from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from src.credentials import read_curius_jwt
from src.logging import get_logger

CURIUS_API_URL = "https://curius.app/api"
logger = get_logger(__name__)


class UserNotFoundError(Exception):
    pass


class CuriusAPIClient:
    def __init__(self, base_url: str = CURIUS_API_URL):
        self.base_url = base_url
        self._session = requests.Session()
        self._token: Optional[str] = None

    def _auth_headers(self) -> Optional[Dict[str, str]]:
        if self._token is None:
            self._token = read_curius_jwt()
        if not self._token:
            return None
        return {"Authorization": f"Bearer {self._token}"}

    def get_user_payload(self, user_link: str) -> Dict[str, Any]:
        logger.debug("Fetching user payload for %s", user_link)
        response = self._session.get(
            f"{self.base_url}/users/{user_link}",
            headers=self._auth_headers(),
        )
        if response.status_code != 200:
            logger.error(
                "User %s not found with status code %s",
                user_link,
                response.status_code,
            )
            raise UserNotFoundError(
                f"User {user_link} not found with status code {response.status_code}"
            )
        return response.json()

    def get_user_dict(self, user_link: str) -> Dict[str, Any]:
        payload = self.get_user_payload(user_link)
        if "user" not in payload:
            raise UserNotFoundError(
                f"Payload retrieved for user {user_link} but 'user' key not found"
            )
        return payload["user"]

    def get_link_payload(self, user_id: int) -> Dict[str, Any]:
        logger.debug("Fetching links payload for user_id=%s", user_id)
        response = self._session.get(
            f"{self.base_url}/users/{user_id}/links",
            headers=self._auth_headers(),
        )
        if response.status_code != 200:
            logger.error(
                "User %s not found with status code %s",
                user_id,
                response.status_code,
            )
            raise UserNotFoundError(
                f"User {user_id} not found with status code {response.status_code}"
            )
        return response.json()

    def get_links_dicts(self, user_id: int) -> List[Dict[str, Any]]:
        payload = self.get_link_payload(user_id)
        if "userSaved" not in payload:
            raise UserNotFoundError(
                f"Payload retrieved for user {user_id} but 'user' key not found"
            )
        return payload["userSaved"]

    def get_links_page_payload(self, user_id: int, page: int) -> Dict[str, Any]:
        logger.debug("Fetching links page=%s for user_id=%s", page, user_id)
        response = self._session.get(
            f"{self.base_url}/users/{user_id}/links",
            params={"page": page},
            headers=self._auth_headers(),
        )
        if response.status_code == 200:
            return response.json()

        logger.error(
            "Links page %s not found for user_id=%s with status code %s",
            page,
            user_id,
            response.status_code,
        )
        raise UserNotFoundError(
            f"Links page {page} not found for user {user_id} with status code {response.status_code}"
        )

    def links_page(self, user_id: int, page: int) -> List[Dict[str, Any]]:
        payload = self.get_links_page_payload(user_id, page)
        for key in ("links", "items", "data", "userSaved"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
        if isinstance(payload.get("results"), list):
            return payload["results"]
        raise UserNotFoundError("Links page payload did not contain a links list")

    def get_network_payload(self, url: str) -> Dict[str, Any]:
        logger.debug("Fetching network payload for url=%s", url)
        response = self._session.post(
            f"{self.base_url}/links/url/network",
            json={"url": url},
            headers=self._auth_headers(),
        )
        if response.status_code == 200:
            return response.json()

        logger.error(
            "Network payload not found for url %s with status code %s",
            url,
            response.status_code,
        )
        raise UserNotFoundError(
            f"Network payload not found for url {url} with status code {response.status_code}"
        )


CuriusAPI = CuriusAPIClient()
