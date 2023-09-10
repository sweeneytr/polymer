import datetime
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Annotated, Any, Generic, Iterable, Self, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import Session

from polymer.connectors.db import DbProxy

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
O = TypeVar("O")
M = TypeVar("M", bound=BaseModel)


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


class Pager:
    def __init__(
        self, response: Response, db: DbProxyDep, pagination: PaginationDep
    ) -> None:
        self.response = response
        self.db = db
        self.pagination = pagination

    def list(self, Model: Type[M], stmt: Iterable[Any]) -> Iterable[M]:
        count = self.db.count(stmt)
        orms = self.db.all_or_paginated(stmt, self.pagination)

        self.response.headers.append("X-Total-Count", str(count))
        return [Model.model_validate(o, from_attributes=True) for o in orms]


class One(Generic[M]):
    def __init__(self, db: DbProxyDep) -> None:
        self.db = db

    def one(self, Model: Type[M], stmt: Iterable[Any]) -> Iterable[M]:
        orm = self.db.one(stmt)
        return Model.model_validate(orm, from_attributes=True)


@router.get("/assets")
async def asset_list(
    pager: Annotated[Pager, Depends()],
    stmt: Annotated[Select[tuple[Asset]], Depends(Asset.select_all)],
) -> list[AssetModel]:
    return pager.list(AssetModel, stmt)


@router.get("/assets/{id}")
async def asset(
    one: Annotated[One, Depends()],
    stmt: Annotated[Select[tuple[Asset]], Depends(Asset.select_one)],
) -> AssetModel:
    return one.one(stmt)


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
    pager: Annotated[Pager, Depends()],
    stmt: Annotated[Select[tuple[Download]], Depends(Download.select_all)],
) -> list[DownloadModel]:
    return pager.list(DownloadModel, stmt)


@router.get("/downloads/{id}")
async def get_download(id: str, db: DbProxyDep) -> DownloadModel:
    orm = db.one(Download.select_one(id))
    return DownloadModel.model_validate(orm, from_attributes=True)


@router.get("/tags")
async def tag_list(
    pager: Annotated[Pager, Depends()],
    stmt: Annotated[Select[tuple[Tag]], Depends(Tag.select_all)],
) -> list[TagModel]:
    return pager.list(TagModel, stmt)


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
    pager: Annotated[Pager, Depends()],
    stmt: Annotated[Select[tuple[User]], Depends(User.select_all)],
) -> list[UserModel]:
    return pager.list(UserModel, stmt)


@router.get("/users/{id}")
async def asset(id: int, db: DbProxyDep) -> UserModel:
    orm = db.one(User.select_one(id))
    return UserModel.model_validate(orm, from_attributes=True)


@router.get("/categories")
async def catagory_list(
    pager: Annotated[Pager, Depends()],
    stmt: Annotated[Select[tuple[Category]], Depends(Category.select_all)],
) -> list[CategoryModel]:
    return pager.list(CategoryModel, stmt)


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
    orm = db.one(Category.select_one(id))
    return CategoryModel.model_validate(orm, from_attributes=True)


@router.delete("/categories/{id}")
async def delete_category(id: int, db: DbProxyDep) -> CategoryModel:
    orm = db.one(Category.select_one(id))
    resp = CategoryModel.model_validate(orm, from_attributes=True)
    db.delete(orm)
    db.commit()
    return resp
