#!/usr/bin/env python

import asyncio
import collections.abc
from contextlib import asynccontextmanager
from itertools import count
from typing import Annotated, Any, Optional, Self

import httpx
import typer
from bs4 import BeautifulSoup

TIME_ZONE = "America/New_York"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"

GRAPHQL = """\
query ListOrders($offset: Int, $limit: Int) {
    me {
        orders(offset: $offset, limit: $limit) {
            id
            lines {
                creation {
                    slug
                }
                downloadUrl 
            }
        }
    }
}

query LikedCreations($offset: Int, $limit: Int) {
    me {
        likedCreations(offset: $offset, limit: $limit) {
            id
            slug
            url
            tags
            price { cents }
        }
    }
}
"""

# with html strings in the loop, seeing locals blows out tracebacks
app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=True)


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


class CultsBase:
    def __init__(
        self,
        client: httpx.AsyncClient,
        email: str,
        password: str,
        time_zone: str | None,
        user_agent: str | None,
    ) -> None:
        self.client = client
        self.email = email
        self.password = password
        self.time_zone = time_zone or TIME_ZONE
        self.user_agent = user_agent or USER_AGENT

        
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
    ) -> BeautifulSoup:
        res = await self.client.post(
            url,
            data=_with_authenticity(data or {}, html),
            headers=_with_csrf(headers or {"User-Agent": self.user_agent}, html),
            params=params,
            follow_redirects=follow_redirects,
        )
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")

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

    async def _find_username(self) -> str:
        html = await self.get_parsed("https://cults3d.com/en/profile/edit")
        return html.find("input", {"name": "users_profile[nick]"})["value"]

    async def _create_api_key(self) -> str:
        html = await self.get_parsed("https://cults3d.com/en/api/keys")

        res_html = await self.post_parsed(
            "https://cults3d.com/en/api/keys",
            html=html,
            data={"commit": "Create+API+Key"},
            follow_redirects=True,
        )

        return (
            res_html.find(id="new-api-key")
            .find("span", {"data-copy-target": "text"})
            .text.strip()
        )

    async def _delete_api_key(self, api_key: str) -> None:
        html = await self.get_parsed("https://cults3d.com/en/api/keys")

        for key in html.findAll("tr", id=lambda x: x and x.startswith("api_key_")):
            key_prefix = key.find("code").text.strip().rstrip("*")

            if api_key.startswith(key_prefix):
                href = key.find("a", {"data-method": "delete"})["href"]
                await self.post_parsed(
                    f"https://cults3d.com{href}", html=html, data={"_method": "delete"}
                )
                break
        else:
            # couldn't find api key?
            pass

    @asynccontextmanager
    async def _with_api_key(self) -> collections.abc.AsyncIterator[str]:
        try:
            key = await self._create_api_key()
            yield key
        finally:
            await self._delete_api_key(key)


class CultsClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        email: str,
        password: str,
        time_zone: str | None,
        user_agent: str | None,
    ) -> None:
        self.client = client
        self.email = email
        self.password = password
        self.time_zone = time_zone or TIME_ZONE
        self.user_agent = user_agent or USER_AGENT

    @asynccontextmanager
    @classmethod
    async def create(
        cls,
        client: httpx.AsyncClient,
        email: str,
        password: str,
        time_zone: str | None,
        user_agent: str | None,
    ) -> collections.abc.AsyncIterator[Self]:
        self = cls(client, email, password, time_zone, user_agent)
        username = await self._find_username()

        async with self._with_api_key() as api_key:
            self.api_key = api_key
            self.username = username
            yield self

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
    ) -> BeautifulSoup:
        res = await self.client.post(
            url,
            data=_with_authenticity(data or {}, html),
            headers=_with_csrf(headers or {"User-Agent": self.user_agent}, html),
            params=params,
            follow_redirects=follow_redirects,
        )
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")

    async def graphql(self, operation: str, **variables: str) -> Any:
        res = await self.client.post(
            "https://cults3d.com/graphql",
            auth=(self.username, self.api_key),
            json={
                "query": GRAPHQL,
                "operationName": operation,
                "variables": variables,
            },
        )
        res.raise_for_status()
        return res.json()

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

    async def _find_username(self) -> str:
        html = await self.get_parsed("https://cults3d.com/en/profile/edit")
        return html.find("input", {"name": "users_profile[nick]"})["value"]

    async def _create_api_key(self) -> str:
        html = await self.get_parsed("https://cults3d.com/en/api/keys")

        res_html = await self.post_parsed(
            "https://cults3d.com/en/api/keys",
            html=html,
            data={"commit": "Create+API+Key"},
            follow_redirects=True,
        )

        return (
            res_html.find(id="new-api-key")
            .find("span", {"data-copy-target": "text"})
            .text.strip()
        )

    async def _delete_api_key(self, api_key: str) -> None:
        html = await self.get_parsed("https://cults3d.com/en/api/keys")

        for key in html.findAll("tr", id=lambda x: x and x.startswith("api_key_")):
            key_prefix = key.find("code").text.strip().rstrip("*")

            if api_key.startswith(key_prefix):
                href = key.find("a", {"data-method": "delete"})["href"]
                await self.post_parsed(
                    f"https://cults3d.com{href}", html=html, data={"_method": "delete"}
                )
                break
        else:
            # couldn't find api key?
            pass

    @asynccontextmanager
    async def _with_api_key(self) -> collections.abc.AsyncIterator[str]:
        try:
            key = await self._create_api_key()
            yield key
        finally:
            await self._delete_api_key(key)

    async def _free_order(self, creation: str) -> None:
        html = await self.get_parsed("https://cults3d.com")

        await self.post_parsed(
            f"https://cults3d.com/en/free_orders",
            html=html,
            params={"creation_slug": creation},
        )

    async def _download_order(self, order: str, creation: str) -> None:
        await self.client.get(f"https://cults3d.com/en/free_orders")

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


async def _main(email, password, timezone, user_agent):
    async with httpx.AsyncClient() as client:
        client = CultsClient(client, email, password, timezone, user_agent)
        await client.login()
        username = await client._find_username(client)

        async with client._with_api_key(client) as api_key:
            orders = await client._get_orders(client, username, api_key)
            creations = client._flatten_orders(orders)
            liked = await client._get_liked(client, username, api_key)

            existing = set()
            for creation in creations:
                slug = creation["slug"]
                existing.add(slug)
                print(f"found order for {slug}")

            for creation in liked:
                slug = creation["slug"]
                if slug in existing:
                    print("skipping creation")
                    continue

                if creation["price"]["cents"] == 0:
                    await client._free_order(client, slug)
                    existing.add(slug)
                    print(f"ordered {slug}")


@app.command()
def main(
    email: str,
    password: Annotated[
        str, typer.Option(prompt=True, confirmation_prompt=True, hide_input=True)
    ],
    timezone: Annotated[Optional[str], typer.Option()] = None,
    user_agent: Annotated[Optional[str], typer.Option()] = None,
) -> None:
    asyncio.run(_main(email, password, timezone, user_agent))


if __name__ == "__main__":
    app()
