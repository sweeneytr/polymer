from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Self, TypeVar

from fastapi import HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base, tag_association_table

if TYPE_CHECKING:
    from .asset import Asset


T = TypeVar("T")


@dataclass
class TagSearch:
    asset_id: int | None = None
    q: str | None = None
    id: Annotated[list[int] | None, Query()] = None


@dataclass
class TagSort:
    _order: Annotated[str, Query()] = "ASC"
    _sort: Annotated[str, Query()] = "id"


class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str]

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="tags", secondary=tag_association_table
    )
    asset_ids: AssociationProxy[list[int]] = association_proxy("tags", "id")

    @classmethod
    def search(cls, stmt: Select[T], search: TagSearch) -> Select[T]:
        if search.q is not None:
            stmt = stmt.where(cls.label.icontains(search.q))

        if search.id is not None:
            stmt = stmt.where(cls.id.in_(search.id))

        return stmt

    @classmethod
    def sort(cls, stmt: Select[T], sort: TagSort) -> Select[T]:
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
    def select_all(cls, search: TagSearch, sort: TagSort) -> Select[tuple[Self]]:
        stmt = select(cls)
        stmt = cls.search(stmt, search)
        stmt = cls.sort(stmt, sort)
        return stmt
