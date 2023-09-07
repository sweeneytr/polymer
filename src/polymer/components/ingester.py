#!/usr/bin/env python

from asyncio import Queue
from logging import getLogger
from typing import Any, NoReturn

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..cults_models import AssetFromCults, OrderFromCults
from ..orm import Asset, Illustration, Tag, User

logger = getLogger(__name__)


class Ingester:
    def __init__(
        self, session: Session, queue: Queue[AssetFromCults | OrderFromCults]
    ) -> None:
        self.session = session
        self.queue = queue

    def get_asset(self, slug: str) -> Asset | None:
        asset_ = self.session.execute(
            select(Asset).filter_by(slug=slug)
        ).scalar_one_or_none()

        return asset_

    def asset_from_cults(self, data: AssetFromCults) -> Asset:
        tags = []
        for label in data.tags:
            tag_ = self.session.execute(
                select(Tag).filter_by(label=label)
            ).scalar_one_or_none()
            if tag_:
                tags.append(tag_)
            else:
                tag_ = Tag(label=label)
                tags.append(tag_)

        user = self.session.execute(
            select(User).filter_by(nickname=data.creator.nickname)
        ).scalar_one_or_none()
        if not user:
            user = User(nickname=data.creator.nickname)

        illustrations = [Illustration(src=i.src) for i in data.illustrations]

        return Asset(
            name=data.name,
            slug=data.slug,
            details=data.details,
            description=data.description,
            cents=data.cents,
            creator=user,
            tags=tags,
            illustrations=illustrations,
        )

    async def run(self) -> NoReturn:
        while True:
            data = await self.queue.get()

            match data:
                case AssetFromCults():
                    asset = self.get_asset(data.slug)
                    if asset is None:
                        asset = self.asset_from_cults(data)
                        self.session.add(asset)

                    logger.debug(f"Processed asset {asset.slug} from cults")

                case OrderFromCults():
                    asset = self.get_asset(data.creation.slug)

                    if asset is None:
                        asset = self.asset_from_cults(data.creation)
                        asset.yanked = True
                        self.session.add(asset)

                    asset.download_url = data.download_url

                    logger.debug(f"Processed order for {asset.slug} from cults")

            self.session.commit()

            self.queue.task_done()
