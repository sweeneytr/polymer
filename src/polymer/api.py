import datetime
from functools import reduce
from logging import getLogger
from pathlib import Path
from typing import Annotated

from fastapi import HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .app import app
from .config import settings
from .lifespan import manager
from .models import AssetModel, TagModel, TaskModel, UserModel
from .orm import Asset, Tag, User, engine

logger = getLogger(__name__)


@app.get("/assets")
async def asset_list(
    response: Response,
    _start: int = 0,
    _end: int = 10,
    _order: str = "ASC",
    _sort: str = "id",
    creator_id: int | None = None,
    tag_id: int | None = None,
    yanked: bool | None = None,
    downloaded: bool | None = None,
    free: bool | None = None,
    q: str | None = None,
    id: Annotated[list[int] | None, Query()] = None,
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

        if tag_id is not None:
            stmt = stmt.where(Asset.tag_ids.any(Tag.id == tag_id))

        if creator_id is not None:
            stmt = stmt.where(Asset.creator_id == creator_id)

        if q is not None:
            conds = [
                f.ilike(f"%{q}%")
                for f in (
                    Asset.slug,
                    Asset.name,
                    Asset.creator,
                    Asset.description,
                    Asset.details,
                )
            ]
            stmt = stmt.where(reduce(lambda a, b: or_(a, b), conds))

        if id is not None:
            stmt = stmt.where(Asset.id.in_(id))

        count = session.execute(select(func.count()).select_from(stmt)).scalar_one()

        if id is None:
            stmt = stmt.offset(_start).limit(_end)

        assets = (
            session.execute(
                stmt.order_by(
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


@app.get("/assets/{id}")
async def asset(id: int) -> AssetModel:
    with Session(engine) as session:
        asset = session.execute(select(Asset).filter_by(id=id)).scalar_one()
        return AssetModel.model_validate(asset, from_attributes=True)


@app.get("/tags")
async def tag_list(
    response: Response,
    _start: int = 0,
    _end: int = 10,
    _order: str = "ASC",
    _sort: str = "id",
    q: str | None = None,
    id: Annotated[list[int] | None, Query()] = None,
) -> list[TagModel]:
    with Session(engine) as session:
        sort_field = getattr(Tag, _sort)
        stmt = select(Tag)

        if q is not None:
            stmt = stmt.where(Tag.label.ilike("%{q}%"))

        if id is not None:
            stmt = stmt.where(Tag.id.in_(id))

        count = session.execute(select(func.count()).select_from(stmt)).scalar_one()

        if id is None:
            stmt = stmt.offset(_start).limit(_end)

        tags = (
            session.execute(
                stmt.order_by(
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


@app.get("/tags/{id}")
async def tag(id: int) -> TagModel:
    with Session(engine) as session:
        tag = session.execute(select(Tag).filter_by(id=id)).scalar_one()
        return TagModel.model_validate(tag, from_attributes=True)


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
    tasks = [
        TaskModel(
            id=i,
            name=s.callable.__qualname__,
            cron=s.cron,
            startup=s.startup,
            last_run_at=datetime.datetime.fromtimestamp(s.last_run_at)
            if s.last_duration
            else None,
            last_duration=s.last_duration if s.last_duration else None,
        )
        for i, s in enumerate(manager.specs)
    ]
    response.headers.append("X-Total-Count", str(len(tasks)))
    return tasks


@app.post("/tasks/{id}/run-now")
async def task_run(id: int) -> None:
    spec = manager.specs[id]
    manager._start_task(spec)
    return


@app.get("/users")
async def users_list(
    response: Response,
    _start: int = 0,
    _end: int = 10,
    _order: str = "ASC",
    _sort: str = "id",
    q: str | None = None,
    id: Annotated[list[int] | None, Query()] = None,
) -> list[UserModel]:
    with Session(engine) as session:
        sort_field = getattr(User, _sort)
        stmt = select(User)

        if q is not None:
            stmt = stmt.where(User.nickname.ilike(f"%{q}%"))

        logger.warning(id)
        if id is not None:
            stmt = stmt.where(User.id.in_(id))

        count = session.execute(select(func.count()).select_from(stmt)).scalar_one()

        if id is None:
            stmt = stmt.offset(_start).limit(_end)

        orms = (
            session.execute(
                stmt.order_by(
                    sort_field.asc()
                    if _order.casefold() == "asc".casefold()
                    else sort_field.desc()
                )
            )
            .scalars()
            .all()
        )
        response.headers.append("X-Total-Count", str(count))
        return [UserModel.model_validate(a, from_attributes=True) for a in orms]


@app.get("/users/{id}")
async def asset(id: int) -> UserModel:
    with Session(engine) as session:
        orm = session.execute(select(User).filter_by(id=id)).scalar_one()
        return UserModel.model_validate(orm, from_attributes=True)
