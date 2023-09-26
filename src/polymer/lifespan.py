import asyncio
import time
from asyncio import Queue, Task, create_task
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from logging import getLogger

import aiocron
import httpx
from fastapi import FastAPI
from sqlalchemy.orm import Session

from alembic import command
from alembic.config import Config
from polymer.connectors.cults_client import CultsGraphQLClient

from .components.actor import Actor
from .components.ingester import Ingester
from .components.scraper import Scraper
from .connectors.cults_client import CultsClient, CultsGraphQLClient
from .orms import engine

logger = getLogger(__name__)


@dataclass
class TaskSpec:
    callable: Callable
    cron: str
    startup: bool
    last_run_at: float | None = None
    last_duration: float | None = None


class TaskManager:
    def __init__(self) -> None:
        self.specs: list[TaskSpec] = []
        self.crons = set()
        self.tasks: set[Callable] = set()

    def register(self, callable: Callable, cron: str, startup: bool = False) -> None:
        self.specs.append(TaskSpec(callable, cron, startup))

    def startup(self) -> None:
        for spec in self.specs:
            if spec.startup:
                self._start_task(spec)

            self.crons.add(aiocron.crontab(spec.cron, self._start_task, (spec,)))

    def _start_task(self, spec: TaskSpec) -> Task:
        if spec.callable in self.tasks:
            logger.warning(f"Skipping {spec.callable.__qualname__}, double scheduled")
            return

        self.tasks.add(spec.callable)
        task = create_task(spec.callable())
        spec.last_run_at = time.time()

        def _done_callback(task: Task) -> None:
            spec.last_duration = time.time() - spec.last_run_at
            logger.info(f"Ran {spec.callable.__qualname__} in {spec.last_duration}")
            self.tasks.discard(spec.callable)

        task.add_done_callback(_done_callback)
        return task


manager = TaskManager()
minutely = "* * * * *"


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    config = Config("./alembic.ini")
    command.upgrade(config, "head", tag="skip_log_config")

    def handler(loop, context):
        logger.error(f"Exception in task {context['future']}", exc_info=context['exception'])
        loop.default_exception_handler(context)

    asyncio.get_event_loop().set_exception_handler(handler)

    queue = Queue()

    with Session(engine) as ingester_session, Session(engine) as actor_session:
        async with httpx.AsyncClient() as http_client, httpx.AsyncClient() as http_client_2:
            client = CultsClient(http_client)
            client_ql = CultsGraphQLClient(http_client_2)

            scraper = Scraper(client_ql, queue)
            ingester = Ingester(ingester_session, queue)
            actor = Actor(client, actor_session)

            manager.register(scraper.fetch_liked, minutely, startup=True)
            manager.register(scraper.fetch_orders, minutely)
            manager.register(actor.order_liked_free, minutely)
            manager.register(actor.download_orders, minutely)

            ingester_task = create_task(ingester.run())
            manager.startup()

            yield

            ingester_task.cancel()
