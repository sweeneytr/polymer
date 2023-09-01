import time
from asyncio import create_task
from contextlib import asynccontextmanager
from functools import wraps
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    startup_tasks = set()

    def startup_task(f):
        task = create_task(time_and_log(f)())
        startup_tasks.add(task)
        task.add_done_callback(startup_tasks.discard)

    startup_task(fetch_liked)
    startup_task(download_orders)

    cron_minutely = "* * * * *"
    # cron1 = aiocron.crontab(cron_minutely, time_and_log(fetch_liked))
    # cron2 = aiocron.crontab(cron_minutely, time_and_log(order_liked_free))
    cron3 = aiocron.crontab(cron_minutely, time_and_log(fetch_orders))

    yield
