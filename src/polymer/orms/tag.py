from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base, tag_association_table

if TYPE_CHECKING:
    from .asset import Asset


class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str]

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="tags", secondary=tag_association_table
    )
