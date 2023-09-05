import time
from asyncio import Task, create_task
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import  wraps
from logging import getLogger

import aiocron
from fastapi import FastAPI

from .scrape import (download_orders, fetch_liked, fetch_orders,
                     order_liked_free)

logger = getLogger(__name__)


def time_and_log(f) -> None:
    @wraps(f)
    async def wrapped(*args, **kwargs):
        start = time.time()
        res = await f(*args, **kwargs)
        delta = time.time() - start
        logger.info(f"Ran {f.__qualname__} in {delta}")
        return res

    return wrapped


@dataclass
class TaskSpec:
    callable: Callable
    cron: str
    startup: bool

class TaskManager:
    def __init__(self) -> None:
        self.specs: dict[Callable, TaskSpec] = {}
        self.crons = set()
        self.tasks: set[Task] = set()

    def regulator(self, f) -> None:
        @wraps(f)
        async def wrapped(*args, **kwargs):
            if f in self.tasks:
                logger.warning(f"Skipping {f.__qualname__}, double scheduled")
                return f

            self._start_task(f(*args, **kwargs))

        return wrapped
    
    def register(self, callable: Callable, cron: str, startup: bool = False) -> None:
        self.specs[callable] = TaskSpec(time_and_log(self.regulator(callable)), cron, startup)


    def startup(self) -> None:
        for taskSpec in self.specs.values():
            if taskSpec.startup:
                self._start_task(taskSpec.callable())

            self.crons.add(aiocron.crontab(taskSpec.cron, taskSpec.callable))

    def _start_task(self, coroutine: Coroutine) -> None:
        task = create_task(coroutine)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)





@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    manager = TaskManager()

    minutely = "* * * * *"

    manager.register(fetch_liked,      minutely, startup=True)
    manager.register(order_liked_free, minutely)
    manager.register(fetch_orders,     minutely)
    manager.register(download_orders,  minutely)
    
    manager.startup()

    yield
