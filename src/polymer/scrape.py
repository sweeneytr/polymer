#!/usr/bin/env python

from itertools import count
from logging import getLogger
from pathlib import Path
from typing import Any

import aiometer
import httpx
import pyrfc6266
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .orm import Asset, engine

logger = getLogger(__name__)

TIME_ZONE = "America/New_York"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"

GRAPHQL = """\
query ListOrders($offset: Int, $limit: Int) {
    me {
        orders(offset: $offset, limit: $limit) {
            id
            lines {
                creation {
                    id
                    name
                    details
                    description
                    slug
                    url
                    tags
                    creator {
                        nick
                    }
                    price { cents }
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
            name
            details
            description
            slug
            url
            tags
            creator {
                nick
            }
            price { cents }
        }
    }
}
"""


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
            dest.parent.mkdir(parents=True, exist_ok=True)

            with dest.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

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


def asset_from_cults(data) -> Asset:
    return Asset(
        name=data["name"],
        slug=data["slug"],
        details=data["details"],
        description=data["description"],
        cents=data["price"]["cents"],
        creator=data["creator"]["nick"],
        downloaded=False,
    )


async def fetch_liked() -> None:
    with Session(engine) as session:
        async with httpx.AsyncClient() as http_client:
            client = CultsClient(http_client)
            liked = await client._get_liked()
            for creation in liked:
                pre = session.execute(
                    select(Asset).filter_by(slug=creation["slug"])
                ).scalar_one_or_none()
                if pre is None:
                    asset = asset_from_cults(creation)
                    asset.yanked = False
                    session.add(asset)
        session.commit()


async def order_liked_free() -> None:
    with Session(engine) as session:
        async with httpx.AsyncClient() as http_client:
            client = CultsClient(http_client)
            await client.login()
            liked = session.execute(select(Asset).filter_by(free=True)).scalars().all()

            async with aiometer.amap(
                lambda creation: client._free_order(creation.slug),
                liked,
                max_at_once=1,  # Limit maximum number of concurrently running tasks.
                max_per_second=0.5,  # Limit request rate to not overload the server.
            ):
                pass


async def fetch_orders() -> None:
    with Session(engine) as session:
        async with httpx.AsyncClient() as http_client:
            client = CultsClient(http_client)
            orders = await client._get_orders()

            for order in orders:
                for line in order["lines"]:
                    slug = line["creation"]["slug"]
                    asset = session.execute(
                        select(Asset).filter_by(slug=slug)
                    ).scalar_one_or_none()
                    if asset is None:
                        asset = asset_from_cults(line["creation"])
                        asset.yanked = True
                        session.add(asset)
                    asset.download_url = line["downloadUrl"]
        session.commit()


async def download_orders() -> None:
    with Session(engine) as session:
        downloadable = (
            session.execute(
                select(Asset).where(
                    Asset.download_url.is_not(None),
                    Asset.downloaded == False,
                )
            )
            .scalars()
            .all()
        )

        async with httpx.AsyncClient() as http_client:
            client = CultsClient(http_client)
            await client.login()

            async def _download(creation: Asset) -> Asset:
                await client._download_order(creation.slug, creation.download_url)
                return creation

            async with aiometer.amap(
                _download,
                downloadable,
                max_at_once=1,  # Limit maximum number of concurrently running tasks.
                max_per_second=0.5,  # Limit request rate to not overload the server.
            ) as results:
                async for result in results:
                    result.downloaded = True
                    session.commit()
