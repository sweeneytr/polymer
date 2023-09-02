import asyncio
import time
from asyncio import Task, create_task
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial, wraps
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
class State:
    current: Task | None = None


tasks: dict[Callable, Task] = {}


def regulator(f) -> None:
    @wraps(f)
    async def wrapped(*args, **kwargs):
        if f in tasks:
            logger.warning(f"Skipping {f.__qualname__}, double scheduled")
            return f

        tasks[f] = create_task(f(*args, **kwargs))
        await tasks[f]
        tasks.pop(f)

    return wrapped


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    startup_tasks: set[Task] = set()

    def startup_task(f):
        task = create_task(regulator(time_and_log(f))())
        startup_tasks.add(task)
        task.add_done_callback(startup_tasks.discard)

    startup_tasks |= {startup_task(f) for f in (fetch_liked, download_orders)}

    cron_minutely = "* * * * *"
    crons = {
        aiocron.crontab(cron_minutely, regulator(time_and_log(f)))
        for f in (fetch_liked, order_liked_free, fetch_orders)
    }

    yield
