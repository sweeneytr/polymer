from dataclasses import dataclass
from typing import Annotated, Optional, Self, TypeVar

from fastapi import Depends, HTTPException, Query
from sqlalchemy import ForeignKey, Select, select
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

T = TypeVar("T")


@dataclass
class CategorySearch:
    asset_id: int | None = None
    q: str | None = None
    id: Annotated[list[int] | None, Query()] = None


@dataclass
class CategorySort:
    _order: Annotated[str, Query()] = "ASC"
    _sort: Annotated[str, Query()] = "id"


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    label: Mapped[str]

    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    child_ids: AssociationProxy[int] = association_proxy("children", "id")

    parent: Mapped[Optional["Category"]] = relationship(
        back_populates="children", remote_side=[id]
    )

    @classmethod
    def search(cls, stmt: Select[T], search: CategorySearch) -> Select[T]:
        if search.q is not None:
            stmt = stmt.where(cls.label.ilike(search.q))

        if search.id is not None:
            stmt = stmt.where(cls.id.in_(search.id))

        return stmt

    @classmethod
    def sort(cls, stmt: Select[T], sort: CategorySort) -> Select[T]:
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
        search: Annotated[CategorySearch, Depends()],
        sort: Annotated[CategorySort, Depends()],
    ) -> Select[tuple[Self]]:
        stmt = select(cls)
        stmt = cls.search(stmt, search)
        stmt = cls.sort(stmt, sort)
        return stmt
