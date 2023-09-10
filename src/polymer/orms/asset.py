from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Optional, Self, TypeVar

from fastapi import HTTPException, Query
from sqlalchemy import (
    Boolean,
    ColumnElement,
    ForeignKey,
    Select,
    or_,
    select,
    type_coerce,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base, tag_association_table

if TYPE_CHECKING:
    from .download import Download
    from .illustration import Illustration
    from .tag import Tag
    from .user import User


T = TypeVar("T")


@dataclass
class AssetSearch:
    creator_id: Annotated[int | None, Query()] = None
    tag_id: Annotated[int | None, Query()] = None
    yanked: Annotated[bool | None, Query()] = None
    downloaded: Annotated[bool | None, Query()] = None
    free: Annotated[bool | None, Query()] = None
    q: Annotated[str | None, Query()] = None
    id: Annotated[list[int] | None, Query()] = None


@dataclass
class AssetSort:
    _order: Annotated[str, Query()] = "ASC"
    _sort: Annotated[str, Query()] = "id"


class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    creator_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    details: Mapped[str]
    description: Mapped[str]
    slug: Mapped[str]
    cents: Mapped[int]
    download_url: Mapped[str | None]
    yanked: Mapped[bool]

    downloads: Mapped[list["Download"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    download_ids: AssociationProxy[list[int]] = association_proxy("downloads", "id")

    illustrations: Mapped[list["Illustration"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    illustration_ids: AssociationProxy[list[int]] = association_proxy(
        "illustrations", "id"
    )

    creator: Mapped["User"] = relationship(back_populates="assets")

    tags: Mapped[list["Tag"]] = relationship(
        back_populates="assets", secondary=tag_association_table
    )
    tag_ids: AssociationProxy[list[int]] = association_proxy("tags", "id")

    @property
    def primary_illustration(self) -> Optional["Illustration"]:
        return None if not self.illustrations else self.illustrations[0]

    @hybrid_property
    def free(self) -> bool:
        return self.cents == 0

    @hybrid_property
    def downloaded(self) -> bool:
        return bool(self.downloads)

    @downloaded.inplace.expression
    @classmethod
    def _downloaded_expression(cls) -> ColumnElement[bool]:
        return type_coerce(cls.downloads.any(), Boolean)

    @classmethod
    def search(cls, stmt: Select[T], search: AssetSearch) -> Select[T]:
        from .tag import Tag
        from .user import User

        if search.yanked is not None:
            stmt = stmt.filter_by(yanked=search.yanked)

        if search.downloaded is not None:
            stmt = stmt.filter_by(downloaded=search.downloaded)

        if search.free is not None:
            stmt = stmt.filter_by(free=search.free)

        if search.tag_id is not None:
            stmt = stmt.where(cls.tag_ids.any(Tag.id == search.tag_id))

        if search.creator_id is not None:
            stmt = stmt.where(cls.creator_id == search.creator_id)

        if search.q is not None:
            from .user import User
            stmt = stmt.where(
                or_(
                    *(
                        f.icontains(search.q)
                        for f in (
                            cls.slug,
                            cls.name,
                            cls.description,
                            cls.details,
                        )
                    ),
                    cls.creator.has(User.nickname.icontains(search.q)),
                )
            )

        if search.id is not None:
            stmt = stmt.where(cls.id.in_(search.id))

        return stmt

    @classmethod
    def sort(cls, stmt: Select[T], sort: AssetSort) -> Select[T]:
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
    def select_all(cls, search: AssetSearch, sort: AssetSort) -> Select[tuple[Self]]:
        stmt = select(cls)
        stmt = cls.search(stmt, search)
        stmt = cls.sort(stmt, sort)
        return stmt
