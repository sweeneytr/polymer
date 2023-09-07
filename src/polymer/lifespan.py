import time
from asyncio import Queue, Task, TaskGroup, create_task
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from logging import getLogger

import aiocron
import httpx
from fastapi import FastAPI
from sqlalchemy.orm import Session

from .cults_client import CultsClient
from .ingester import Ingester
from .orm import engine
from .scrape import (download_orders, fetch_liked, fetch_orders,
                     order_liked_free)
from .scraper import Scraper

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

manager.register(order_liked_free, minutely)
manager.register(download_orders, minutely)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    queue = Queue()
    async with TaskGroup() as tg:
        with Session(engine) as ingester_session:
            async with httpx.AsyncClient() as http_client:
                client = CultsClient(http_client)
                scraper = Scraper(client, queue)
                ingester = Ingester(ingester_session, queue)

                manager.register(scraper.fetch_liked, minutely, startup=True)
                manager.register(scraper.fetch_orders, minutely)

                tg.create_task(ingester.run())
                manager.startup()

                yield
