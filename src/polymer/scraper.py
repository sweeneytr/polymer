from asyncio import Queue
from logging import getLogger

from .cults_client import CultsClient
from .cults_models import AssetFromCults, OrderFromCults

logger = getLogger(__name__)


class Scraper:
    def __init__(
        self, client: CultsClient, queue: Queue[AssetFromCults | OrderFromCults]
    ) -> None:
        self.client = client
        self.queue = queue

    async def fetch_liked(self) -> None:
        liked = await self.client._get_liked()
        for creation in liked:
            asset = AssetFromCults.model_validate(creation)
            await self.queue.put(asset)

    async def fetch_orders(self) -> None:
        orders = await self.client._get_orders()
        for order in orders:
            for line in order["lines"]:
                order = OrderFromCults.model_validate(line)
                await self.queue.put(order)
