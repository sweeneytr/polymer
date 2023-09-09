from typing import TYPE_CHECKING

from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .asset import Asset


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str]

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
    asset_ids: AssociationProxy[list[str]] = association_proxy("assets", "id")
