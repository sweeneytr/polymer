import time
from asyncio import Task, create_task
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from logging import getLogger

import aiocron
from fastapi import FastAPI

from .scrape import download_orders, fetch_liked, fetch_orders, order_liked_free

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

manager.register(fetch_liked, minutely, startup=True)
manager.register(order_liked_free, minutely)
manager.register(fetch_orders, minutely)
manager.register(download_orders, minutely)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    manager.startup()
    yield
