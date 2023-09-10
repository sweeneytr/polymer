from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Self, TypeVar

from fastapi import Depends, HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .asset import Asset


T = TypeVar("T")


@dataclass
class UserSearch:
    asset_id: int | None = None
    q: str | None = None
    id: Annotated[list[int] | None, Query()] = None


@dataclass
class UserSort:
    _order: Annotated[str, Query()] = "ASC"
    _sort: Annotated[str, Query()] = "id"


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str]

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
    asset_ids: AssociationProxy[list[str]] = association_proxy("assets", "id")

    @classmethod
    def search(cls, stmt: Select[T], search: UserSearch) -> Select[T]:
        if search.q is not None:
            stmt = stmt.where(cls.nickname.icontains(search.q))

        if search.id is not None:
            stmt = stmt.where(cls.id.in_(search.id))
        return stmt

    @classmethod
    def sort(cls, stmt: Select[T], sort: UserSort) -> Select[T]:
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
        search: Annotated[UserSearch, Depends()],
        sort: Annotated[UserSort, Depends()],
    ) -> Select[tuple[Self]]:
        stmt = select(cls)
        stmt = cls.search(stmt, search)
        stmt = cls.sort(stmt, sort)
        return stmt
