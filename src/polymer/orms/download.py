import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Self, TypeVar

from fastapi import Depends, HTTPException, Query
from sqlalchemy import ForeignKey, Select, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .asset import Asset


T = TypeVar("T")


@dataclass
class DownloadSearch:
    asset_id: int | None = None
    q: str | None = None
    id: Annotated[list[int] | None, Query()] = None


@dataclass
class DownloadSort:
    _order: Annotated[str, Query()] = "ASC"
    _sort: Annotated[str, Query()] = "id"


class Download(Base):
    __tablename__ = "download"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    filename: Mapped[str]
    downloaded_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    asset: Mapped["Asset"] = relationship(back_populates="downloads")

    @property
    def path(self) -> Path:
        return Path(self.asset.slug, self.filename)

    @classmethod
    def search(cls, stmt: Select[T], search: DownloadSearch) -> Select[T]:
        if search.asset_id is not None:
            stmt = stmt.where(cls.asset_id == search.asset_id)

        if search.q is not None:
            pass

        if search.id is not None:
            stmt = stmt.where(cls.id.in_(search.id))

        return stmt

    @classmethod
    def sort(cls, stmt: Select[T], sort: DownloadSort) -> Select[T]:
        sort_field = getattr(cls, sort._sort, None)
        if sort_field is None:
            raise HTTPException(422, f"Unknown sort field {sort._sort}")

        return stmt.order_by(
            sort_field.asc()
            if sort._order.casefold() == "asc".casefold()
            else sort_field.desc()
        )

    @classmethod
    def select_one(cls, id: int) -> Select[tuple[Self]]:
        return select(cls).filter_by(id=id)

    @classmethod
    def select_all(
        cls,
        search: Annotated[DownloadSearch, Depends()],
        sort: Annotated[DownloadSort, Depends()],
    ) -> Select[tuple[Self]]:
        stmt = select(cls)
        stmt = cls.search(stmt, search)
        stmt = cls.sort(stmt, sort)
        return stmt
