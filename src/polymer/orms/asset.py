from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ColumnElement, ForeignKey, type_coerce
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base, tag_association_table

if TYPE_CHECKING:
    from .download import Download
    from .illustration import Illustration
    from .tag import Tag
    from .user import User


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
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    creator: Mapped["User"] = relationship(
        back_populates="assets",
    )

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
