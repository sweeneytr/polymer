from functools import cached_property
from pathlib import Path
from contextvars import ContextVar

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, computed_field
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session
from functools import reduce

from .config import settings
from .lifespan import lifespan
from .orm import Asset, engine, Tag

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
]

request_var: ContextVar[Request] = ContextVar('request_var')

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
        request = request_var.get(None)
        if request is None:
            return None
    
        return str(request.url_for('asset_download', id=self.id))
    

class TagModel(BaseModel):
    id: int
    label: str

class TaskModel(BaseModel):
    name: str
    cron: str

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_var.set(request)
    return await call_next(request)


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
    q: str | None = None,
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
        
        if q is not None:
            conds = [f.ilike(f"%{q}%") for f in (Asset.slug, Asset.name, Asset.creator, Asset.description, Asset.details)]
            stmt = stmt.where(reduce(lambda a, b: or_(a, b), conds))

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

@app.get("/tags")
async def asset_list(
    response: Response,
    _start: int = 0,
    _end: int = 10,
    _order: str = "ASC",
    _sort: str = "id",
    q: str | None = None,
) -> list[TagModel]:
    with Session(engine) as session:
        sort_field = getattr(Tag, _sort)
        stmt = select(Tag)
        
        if q is not None:
            stmt = stmt.where(Tag.label.ilike("%{q}%"))

        count = session.execute(select(func.count()).select_from(stmt)).scalar_one()
        tags = (
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
        return [TagModel.model_validate(t, from_attributes=True) for t in tags]

@app.get("/assets/{id}/download")
async def asset_download(id: str) -> Response:
    with Session(engine) as session:
        asset = session.execute(select(Asset).filter_by(id=id)).scalar_one()

        if not asset.downloaded:
            raise HTTPException(404)

        path = Path(settings.download_dir, asset.slug)
        filepath = next(path.iterdir())

        return FileResponse(filepath, filename=filepath.name)

@app.get("/tasks")
async def task_list(
    response: Response,
    _start: int = 0,
    _end: int = 10,
    _order: str = "ASC",
    _sort: str = "id",
    q: str | None = None,
) -> list[TaskModel]:
    with Session(engine) as session:
        sort_field = getattr(Tag, _sort)
        stmt = select(Tag)
        
        if q is not None:
            stmt = stmt.where(Tag.label.ilike("%{q}%"))

        count = session.execute(select(func.count()).select_from(stmt)).scalar_one()
        tags = (
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
        return [TagModel.model_validate(t, from_attributes=True) for t in tags]
