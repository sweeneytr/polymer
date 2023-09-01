from asyncio import create_task
from contextlib import asynccontextmanager

import aiocron
from fastapi import FastAPI
import time
from logging import getLogger
from .scrape import fetch_liked, fetch_orders, order_liked_free, download_orders
from functools import wraps
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

    task = create_task(time_and_log(fetch_liked)())
    startup_tasks.add(task)
    task.add_done_callback(startup_tasks.discard)

    cron_minutely = "* * * * *"
    cron1 = aiocron.crontab(cron_minutely, time_and_log(fetch_liked))
    cron2 = aiocron.crontab(cron_minutely, time_and_log(order_liked_free))
    cron3 = aiocron.crontab(cron_minutely, time_and_log(fetch_orders))
    cron3 = aiocron.crontab(cron_minutely, time_and_log(download_orders))

    yield
