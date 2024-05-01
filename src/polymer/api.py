import datetime
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Annotated, Any, Generic, Iterable, Self, Type, TypeVar
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import Session

from polymer.connectors.db import DbProxy
from polymer.orms.mmf import Mmf

from .config import Settings, settings
from .lifespan import manager
from .models import (
    AssetModel,
    CategoryCreate,
    CategoryModel,
    CultsModel,
    DownloadModel,
    MmfModel,
    TagModel,
    TaskModel,
    UserModel,
)
from .orms import Asset, Category, Download, Tag, User, engine
from .config import settings

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


class Controller(Generic[M]):
    def __init__(
        self,
        request: Request,
        response: Response,
        db: DbProxyDep,
        pagination: PaginationDep,
    ) -> None:
        self.request = request
        self.response = response
        self.db = db
        self.pagination = pagination

    def list(self, Model: Type[M], stmt: Iterable[Any]) -> Iterable[M]:
        count = self.db.count(stmt)
        orms = self.db.all_or_paginated(stmt, self.pagination)

        self.response.headers.append("X-Total-Count", str(count))
        return [Model.model_validate(o, from_attributes=True) for o in orms]

    def create(self, Model: Type[M], endpoint: str, orm: Any) -> M:
        # orm = Category(label=body.label, parent_id=body.parent_id)
        self.db.add(orm)
        self.db.commit()

        self.response.headers.append(
            "Location", str(self.request.url_for(endpoint, id=orm.id))
        )

        return Model.model_validate(orm, from_attributes=True)

    def one(self, Model: Type[M], stmt: Iterable[Any]) -> M:
        orm = self.db.one(stmt)
        return Model.model_validate(orm, from_attributes=True)

    def delete(self, Model: Type[M], stmt: Iterable[Any]) -> M:
        orm = self.db.one(stmt)
        resp = Model.model_validate(orm, from_attributes=True)
        self.db.delete(orm)
        self.db.commit()
        return resp


ControllerDep = Annotated[Controller, Depends()]
MmfController = Annotated[Controller[Mmf], Depends()]

AllAssetsDep = Annotated[Select[tuple[Asset]], Depends(Asset.select_all)]
OneAssetDep = Annotated[Select[tuple[Asset]], Depends(Asset.select_one)]

AllDownloadsDep = Annotated[Select[tuple[Download]], Depends(Download.select_all)]
OneDownloadDep = Annotated[Select[tuple[Download]], Depends(Download.select_one)]

AllTagsDep = Annotated[Select[tuple[Tag]], Depends(Tag.select_all)]
OneTagDep = Annotated[Select[tuple[Tag]], Depends(Tag.select_one)]

AllUsersDep = Annotated[Select[tuple[User]], Depends(User.select_all)]
OneUserDep = Annotated[Select[tuple[User]], Depends(User.select_one)]

AllCatagoriesDep = Annotated[Select[tuple[Category]], Depends(Category.select_all)]
OneCatagoryDep = Annotated[Select[tuple[Category]], Depends(Category.select_one)]

OneMmfDep = Annotated[Select[tuple[Mmf]], Depends(Mmf.select_one)]

@router.get("/assets")
async def asset_list(controller: ControllerDep, stmt: AllAssetsDep) -> list[AssetModel]:
    return controller.list(AssetModel, stmt)


@router.get("/assets/{id}")
async def asset(controller: ControllerDep, stmt: OneAssetDep) -> AssetModel:
    return controller.one(AssetModel, stmt)


@router.get("/assets/{id}/download")
async def asset_download(db: DbProxyDep, stmt: OneAssetDep) -> Response:
    orm = db.one(stmt)

    if not orm.downloaded:
        raise HTTPException(404)

    path = Path(settings.download_dir, orm.slug)
    filepath = next(path.iterdir())

    return FileResponse(filepath, filename=filepath.name)


@router.get("/downloads")
async def downloads_list(
    controller: ControllerDep, stmt: AllDownloadsDep
) -> list[DownloadModel]:
    return controller.list(DownloadModel, stmt)


@router.get("/downloads/{id}")
async def get_download(
    controller: ControllerDep, stmt: OneDownloadDep
) -> DownloadModel:
    return controller.one(DownloadModel, stmt)


@router.get("/tags")
async def tag_list(controller: ControllerDep, stmt: AllTagsDep) -> list[TagModel]:
    return controller.list(TagModel, stmt)


@router.get("/tags/{id}")
async def tag(controller: ControllerDep, stmt: OneTagDep) -> TagModel:
    return controller.one(TagModel, stmt)


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
async def users_list(controller: ControllerDep, stmt: AllUsersDep) -> list[UserModel]:
    return controller.list(UserModel, stmt)


@router.get("/users/{id}")
async def asset(controller: ControllerDep, stmt: OneUserDep) -> UserModel:
    return controller.one(UserModel, stmt)


@router.get("/categories")
async def catagory_list(
    controller: ControllerDep, stmt: AllCatagoriesDep
) -> list[CategoryModel]:
    return controller.list(CategoryModel, stmt)


@router.post("/categories", status_code=201)
async def catagory_create(
    controller: ControllerDep, body: CategoryCreate
) -> CategoryModel:
    orm = Category(label=body.label, parent_id=body.parent_id)
    return controller.create(CategoryModel, "get_category", orm)


@router.get("/categories/{id}")
async def get_category(
    controller: ControllerDep, stmt: OneCatagoryDep
) -> CategoryModel:
    return controller.one(CategoryModel, stmt)


@router.delete("/categories/{id}")
async def delete_category(
    controller: ControllerDep, stmt: OneCatagoryDep
) -> CategoryModel:
    return controller.delete(CategoryModel, stmt)


@router.get("/mmf/login")
async def mmf_login(request: Request) -> RedirectResponse:
    state = str(uuid4())
    redirect_uri = request.base_url.replace(path="/api/mmf/callback")
    url = (
        "https://auth.myminifactory.com/web/authorize"
        f"?client_id={settings.mmf_client_id}"
        f"&redirect_uri={str(redirect_uri)}"
        f"&response_type=code"
        f"&state={state}"
    )
    return RedirectResponse(url)


@router.get("/mmf/callback")
async def mmf_callback(request: Request, code: str, state: str, controller: ControllerDep) -> MmfModel:
    url = "https://auth.myminifactory.com/v1/oauth/tokens"
    redirect_uri = request.base_url.replace(path="/api/mmf/callback")
    res = httpx.post(
        url,
        auth=(settings.mmf_client_id, settings.mmf_client_secret),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(redirect_uri),
        },
    )
    data1 = res.json()
    print(data1)

    url2 = "https://auth.myminifactory.com/v1/oauth/introspect"
    res2 = httpx.post(
        url2,
        auth=(settings.mmf_client_id, settings.mmf_client_secret),
        data={
            "token": data1['refresh_token'],
            "token_type_hint": 'refresh_token',
        },
    )
    data2 = res2.json()

    return controller.create(MmfModel, "", Mmf(
        user_id=data1['user_id'],
        access_token=data1['access_token'],
        refresh_token=data1['refresh_token'],
        access_exp=datetime.datetime.now() + datetime.timedelta(milliseconds=data1['expires_in']),
        refresh_exp=datetime.datetime.fromtimestamp(data2['exp'])))

@router.get("/mmf/refresh")
async def mmf_refresh(controller: ControllerDep) -> dict:
    url = "https://auth.myminifactory.com/v1/oauth/tokens"
    res = httpx.post(
        url,
        auth=(settings.mmf_client_id, settings.mmf_client_secret),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
        },
    )
    return res.json()

@router.get("/mmf/status")
async def mmf_refresh(controller: ControllerDep, stmt: OneMmfDep) -> MmfModel:
    return controller.one(MmfModel, stmt)

@router.get("/cults/status")
async def mmf_refresh() -> CultsModel:
    return CultsModel(email=settings.email)