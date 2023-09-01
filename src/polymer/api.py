from functools import cached_property

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, computed_field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .lifespan import lifespan
from .orm import Asset, engine

app = FastAPI(lifespan=lifespan)

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


class AssetModel(BaseModel):
    id: int
    slug: str
    name: str
    details: str
    description: str
    creator: str
    cents: int
    download_url: str | None
    yanked: bool
    downloaded: bool

    @computed_field
    @cached_property
    def free(self) -> bool:
        return self.cents == 0


@app.get("/assets")
async def asset_list(response: Response) -> list[AssetModel]:
    with Session(engine) as session:
        assets = session.execute(select(Asset)).scalars().all()
        response.headers.append("X-Total-Count", str(len(assets)))
        return [AssetModel.model_validate(a, from_attributes=True) for a in assets]
