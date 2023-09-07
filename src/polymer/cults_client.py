from importlib.resources import files
from itertools import count
from logging import getLogger
from pathlib import Path
from typing import Any

import httpx
import pyrfc6266
from bs4 import BeautifulSoup

from .config import settings

logger = getLogger(__name__)

TIME_ZONE = "America/New_York"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
GRAPHQL = files(__package__).joinpath("cults.graphql").read_text()


def _get_csrf(html: BeautifulSoup) -> str:
    return html.find("meta", {"name": "csrf-token"})["content"]


def _get_authenticity(html: BeautifulSoup) -> str:
    return html.find("input", {"name": "authenticity_token"})["value"]


def _with_csrf(data: dict[str, Any], html: BeautifulSoup) -> dict[str, Any]:
    data.update({"X-CSRF-Token": _get_csrf(html)})
    return data


def _with_authenticity(data: dict[str, Any], html: BeautifulSoup) -> dict[str, Any]:
    data.update({"authenticity_token": _get_authenticity(html)})
    return data


class CultsInfra:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self.email = settings.email
        self.password = settings.password
        self.time_zone = TIME_ZONE
        self.user_agent = USER_AGENT
        self.nickname = settings.nickname
        self.api_key = settings.apikey

    async def login(self) -> None:
        html = await self.get_parsed("https://cults3d.com/en/users/sign-in")

        # Session state is cookie based, just need to post a sign-in
        await self.post_parsed(
            "https://cults3d.com/en/users/sign-in",
            html=html,
            data={
                "user[email]": self.email,
                "user[password]": self.password,
                "user[time_zone]": self.time_zone,
                "commit": "Sign in",
            },
            follow_redirects=True,
        )

    async def get_parsed(self, url: str) -> BeautifulSoup:
        res = await self.client.get(url)
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")

    async def post_parsed(
        self,
        url: str,
        *,
        html: BeautifulSoup,
        data: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        follow_redirects: bool = False,
        ignore_error: bool = False,  # custom, sign-in will 400 even when it works sometime
    ) -> BeautifulSoup:
        res = await self.client.post(
            url,
            data=_with_authenticity(data or {}, html),
            headers=_with_csrf(headers or {"User-Agent": self.user_agent}, html),
            params=params,
            follow_redirects=follow_redirects,
        )
        if not ignore_error:
            res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")

    async def graphql(self, operation: str, **variables: str) -> Any:
        res = await self.client.post(
            "https://cults3d.com/graphql",
            auth=(self.nickname, self.api_key),
            json={
                "query": GRAPHQL,
                "operationName": operation,
                "variables": variables,
            },
        )
        res.raise_for_status()
        return res.json()


class CultsClient(CultsInfra):
    async def _free_order(self, creation: str) -> None:
        html = await self.get_parsed("https://cults3d.com")

        await self.post_parsed(
            f"https://cults3d.com/en/free_orders",
            html=html,
            params={"creation_slug": creation},
            follow_redirects=True,
        )

    async def _download_order(self, slug: str, download_url: str) -> None:
        async with self.client.stream(
            "GET", download_url, follow_redirects=True
        ) as response:
            filename = pyrfc6266.parse_filename(response.headers["Content-Disposition"])

            dest = Path(settings.download_dir).joinpath(slug, filename)
            if dest.exists():
                return filename

            dest.parent.mkdir(parents=True, exist_ok=True)

            with dest.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

        return filename

    async def _get_orders(self) -> list:
        _result = []
        limit = 100

        for offset in count(step=limit):
            data = await self.graphql("ListOrders", offset=offset, limit=limit)

            orders = data["data"]["me"]["orders"]
            _result.extend(orders)

            if len(orders) < limit:
                break

        return _result

    def _flatten_orders(self, orders: list) -> list[str]:
        return [line["creation"] for order in orders for line in order["lines"]]

    async def _get_liked(self) -> list:
        _result = []
        limit = 100

        for offset in count(step=limit):
            data = await self.graphql("LikedCreations", offset=offset, limit=limit)

            liked = data["data"]["me"]["likedCreations"]
            _result.extend(liked)

            if len(liked) < limit:
                break

        return _result
