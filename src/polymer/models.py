import datetime
from contextvars import ContextVar
from functools import cached_property

from fastapi import Request
from pydantic import AliasPath, BaseModel, Field, computed_field

request_var: ContextVar[Request] = ContextVar("request_var")


class IllustrationModel(BaseModel):
    src: str


class AssetModel(BaseModel):
    id: int
    slug: str
    name: str
    details: str
    description: str
    creator: str = Field(validation_alias=AliasPath("creator", "nickname"))
    creator_id: int
    cents: int
    download_url: str | None
    yanked: bool
    downloaded: bool
    illustration_url: str | None = Field(
        default=None, validation_alias=AliasPath("primary_illustration", "src")
    )
    illustrations: list[IllustrationModel]
    tag_ids: list[int]

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

        if not self.downloaded:
            return None

        return str(request.url_for("asset_download", id=self.id))


class TagModel(BaseModel):
    id: int
    label: str


class UserModel(BaseModel):
    id: int
    nickname: str
    asset_ids: list[int]


class TaskModel(BaseModel):
    id: int
    name: str
    cron: str
    startup: bool
    last_run_at: datetime.datetime | None
    last_duration: float | None

    @computed_field
    @cached_property
    def run_url(self) -> str | None:
        request = request_var.get(None)
        if request is None:
            return None

        return str(request.url_for("task_run", id=self.id))


class CategoryCreate(BaseModel):
    parent_id: int | None = None
    label: str


class CategoryModel(BaseModel):
    id: int
    parent_id: int | None
    child_ids: list[int]
    label: str
