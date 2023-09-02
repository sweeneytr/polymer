from functools import cached_property
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, computed_field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
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

    @computed_field
    @cached_property
    def nab_url(self) -> str | None:
        if self.downloaded:
            return f"/assets/{self.id}/download"


@app.get("/assets")
async def asset_list(
    response: Response,
    _start: int = 0,
    _end: int = 10,
    _order: str = "ASC",
    _sort: str = "id",
    yanked: bool | None = None,
    downloaded: bool | None = None,
    free: bool | None = None,
) -> list[AssetModel]:
    with Session(engine) as session:
        sort_field = getattr(Asset, _sort)
        stmt = select(Asset)
        
        if yanked is not None:
            stmt = stmt.filter_by(yanked=yanked)
        
        if downloaded is not None:
            stmt = stmt.filter_by(downloaded=downloaded)
        
        if free is not None:
            stmt = stmt.filter_by(free=free)

        count = session.execute(select(func.count()).select_from(stmt)).scalar_one()
        assets = (
            session.execute(
                stmt
                .offset(_start)
                .limit(_end)
                .order_by(
                    sort_field.asc()
                    if _order.casefold() == "asc".casefold()
                    else sort_field.desc()
                )
            )
            .scalars()
            .all()
        )
        response.headers.append("X-Total-Count", str(count))
        return [AssetModel.model_validate(a, from_attributes=True) for a in assets]


@app.get("/assets/{id}/download")
async def asset_list(id: str) -> Response:
    with Session(engine) as session:
        asset = session.execute(select(Asset).filter_by(id=id)).scalar_one()

        if not asset.downloaded:
            raise HTTPException(404)

        path = Path(settings.download_dir, asset.slug)
        filepath = next(path.iterdir())

        return FileResponse(filepath, filename=filepath.name)
