from logging import getLogger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .lifespan import lifespan
from .models import request_var as model_request_var

app = FastAPI(lifespan=lifespan)

logger = getLogger(__name__)

origins = [
    "http://localhost:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def model_middleware(request: Request, call_next):
    model_request_var.set(request)
    return await call_next(request)


app.include_router(router)
