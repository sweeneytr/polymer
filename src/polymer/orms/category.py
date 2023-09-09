from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    parent: Mapped[Optional["Category"]] = relationship(
        back_populates="children", remote_side=[id]
    )
    label: Mapped[str]

    child_ids: AssociationProxy[int] = association_proxy("children", "id")
