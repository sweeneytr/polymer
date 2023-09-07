from logging import getLogger

import aiometer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .cults_client import CultsClient
from .orm import Asset, Download

logger = getLogger(__name__)

class Actor:
    def __init__(
        self, client: CultsClient, session: Session,
    ) -> None:
        self.client = client
        self.session = session

    async def order_liked_free(self) -> None:
        await self.client.login()
        liked = (
            self.session.execute(select(Asset).filter_by(free=True, downloaded=False))
            .scalars()
            .all()
        )

        async with aiometer.amap(
            lambda creation: self.client._free_order(creation.slug),
            liked,
            max_at_once=1,  # Limit maximum number of concurrently running tasks.
            max_per_second=0.5,  # Limit request rate to not overload the server.
        ):
            pass



    async def download_orders(self) -> None:
        downloadable = (
            self.session.execute(
                select(Asset).where(
                    Asset.download_url.is_not(None),
                    Asset.downloaded == False,
                )
            )
            .scalars()
            .all()
        )

        await self.client.login()

        async def _download(creation: Asset) -> Asset:
            filename = await self.client._download_order(
                creation.slug, creation.download_url
            )
            creation.downloads.append(Download(filename=filename))

            self.session.commit()
            return creation

        async with aiometer.amap(
            _download,
            downloadable,
            max_at_once=3,  # Limit maximum number of concurrently running tasks.
            max_per_second=0.5,  # Limit request rate to not overload the server.
    ) as results:
                pass
