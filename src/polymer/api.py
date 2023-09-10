import datetime
from dataclasses import dataclass
from functools import reduce
from logging import getLogger
from pathlib import Path
from typing import Annotated, Any, Self, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from polymer.connectors.db import DbProxy
from polymer.orms.asset import AssetSearch, AssetSort
from polymer.orms.category import CategorySearch, CategorySort
from polymer.orms.download import DownloadSearch, DownloadSort
from polymer.orms.tag import TagSearch, TagSort
from polymer.orms.user import UserSearch, UserSort

from .config import settings
from .lifespan import manager
from .models import (
    AssetModel,
    CategoryCreate,
    CategoryModel,
    DownloadModel,
    TagModel,
    TaskModel,
    UserModel,
)
from .orms import Asset, Category, Download, Tag, User, engine

logger = getLogger(__name__)

router = APIRouter()

T = TypeVar("T")


def db_proxy():
    with Session(engine) as session:
        yield DbProxy(session)


@dataclass
class Pagination:
    offset: int
    limit: int

    @classmethod
    def get(
        cls,
        _start: Annotated[int | None, Query()] = None,
        _end: Annotated[int | None, Query()] = None,
    ) -> Self | None:
        if _start is not None and _end is not None:
            return cls(_start, _end)

        return None


DbProxyDep = Annotated[DbProxy, Depends(db_proxy)]
PaginationDep = Annotated[Pagination | None, Depends(Pagination.get)]


@dataclass
class Sort:
    _order: Annotated[str, Query()] = "ASC"
    _sort: Annotated[str, Query()] = "id"

    def apply(self, cls: Any, stmt: Select[T]) -> Select[T]:
        sort_field = getattr(cls, self._sort, None)
        if sort_field is None:
            raise HTTPException(422, f"Unknown sort field {self._sort}")

        return stmt.order_by(
            sort_field.asc()
            if self._order.casefold() == "asc".casefold()
            else sort_field.desc()
        )


@router.get("/assets")
async def asset_list(
    response: Response,
    db: DbProxyDep,
    pagination: PaginationDep,
    sort: Annotated[AssetSort, Depends()],
    search: Annotated[AssetSearch, Depends()],
) -> list[AssetModel]:
    stmt = Asset.select_all(search, sort)
    count = db.count(stmt)
    orms = db.all_or_paginated(stmt, pagination)

    response.headers.append("X-Total-Count", str(count))
    return [AssetModel.model_validate(o, from_attributes=True) for o in orms]


@router.get("/assets/{id}")
async def asset(id: int, db: DbProxyDep) -> AssetModel:
    orm = db.one(Asset.select_one(id))
    return AssetModel.model_validate(orm, from_attributes=True)


@router.get("/assets/{id}/download")
async def asset_download(id: str, db: DbProxyDep) -> Response:
    orm = db.one(Asset.select_one(id))

    if not orm.downloaded:
        raise HTTPException(404)

    path = Path(settings.download_dir, orm.slug)
    filepath = next(path.iterdir())

    return FileResponse(filepath, filename=filepath.name)


@router.get("/downloads")
async def downloads_list(
    response: Response,
    db: DbProxyDep,
    pagination: PaginationDep,
    sort: Annotated[DownloadSort, Depends()],
    search: Annotated[DownloadSearch, Depends()],
) -> list[DownloadModel]:
    stmt = Download.select_all(search, sort)
    count = db.count(stmt)
    orms = db.all_or_paginated(stmt, pagination)

    response.headers.append("X-Total-Count", str(count))
    return [DownloadModel.model_validate(o, from_attributes=True) for o in orms]


@router.get("/downloads/{id}")
async def get_download(id: str, db: DbProxyDep) -> DownloadModel:
    orm = db.one(Download.select_one(id))
    return DownloadModel.model_validate(orm, from_attributes=True)


@router.get("/tags")
async def tag_list(
    response: Response,
    db: DbProxyDep,
    pagination: PaginationDep,
    sort: Annotated[TagSort, Depends()],
    search: Annotated[TagSearch, Depends()],
) -> list[TagModel]:
    stmt = Tag.select_all(search, sort)
    count = db.count(stmt)
    orms = db.all_or_paginated(stmt, pagination)

    response.headers.append("X-Total-Count", str(count))
    return [TagModel.model_validate(o, from_attributes=True) for o in orms]


@router.get("/tags/{id}")
async def tag(id: int, db: DbProxyDep) -> TagModel:
    orm = db.one(Tag.select_one(id))
    return TagModel.model_validate(orm, from_attributes=True)


@router.get("/tasks")
async def task_list(
    response: Response,
    db: DbProxyDep,
    pagination: PaginationDep,
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


@router.post("/tasks/{id}/run-now")
async def task_run(id: int) -> None:
    spec = manager.specs[id]
    manager._start_task(spec)
    return


@router.get("/users")
async def users_list(
    response: Response,
    db: DbProxyDep,
    pagination: PaginationDep,
    sort: Annotated[UserSort, Depends()],
    search: Annotated[UserSearch, Depends()],
) -> list[UserModel]:
    stmt = User.select_all(search, sort)
    count = db.count(stmt)
    orms = db.all_or_paginated(stmt, pagination)

    response.headers.append("X-Total-Count", str(count))
    return [UserModel.model_validate(o, from_attributes=True) for o in orms]


@router.get("/users/{id}")
async def asset(id: int, db: DbProxyDep) -> UserModel:
    orm = db.one(select(User).filter_by(id=id))
    return UserModel.model_validate(orm, from_attributes=True)


@router.get("/categories")
async def catagory_list(
    response: Response,
    db: DbProxyDep,
    pagination: PaginationDep,
    sort: Annotated[CategorySort, Depends()],
    search: Annotated[CategorySearch, Depends()],
) -> list[CategoryModel]:
    stmt = Category.select_all(search, sort)
    count = db.count(stmt)
    orms = db.all_or_paginated(stmt, pagination)

    response.headers.append("X-Total-Count", str(count))
    return [CategoryModel.model_validate(o, from_attributes=True) for o in orms]


@router.post("/categories", status_code=201)
async def catagory_create(
    request: Request, db: DbProxyDep, response: Response, body: CategoryCreate
) -> CategoryModel:
    category = Category(label=body.label, parent_id=body.parent_id)
    db.add(category)
    db.commit()

    response.headers.append(
        "Location", str(request.url_for("get_category", id=category.id))
    )

    return CategoryModel.model_validate(category, from_attributes=True)


@router.get("/categories/{id}")
async def get_category(id: int, db: DbProxyDep) -> CategoryModel:
    orm = db.one(select(Category).filter_by(id=id))
    return CategoryModel.model_validate(orm, from_attributes=True)


@router.delete("/categories/{id}")
async def delete_category(id: int, db: DbProxyDep) -> CategoryModel:
    orm = db.one(select(Category).filter_by(id=id))
    resp = CategoryModel.model_validate(orm, from_attributes=True)
    db.delete(orm)
    db.commit()
    return resp
