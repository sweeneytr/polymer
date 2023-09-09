from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .asset import Asset


class Illustration(Base):
    __tablename__ = "illustration"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    src: Mapped[str]

    asset: Mapped["Asset"] = relationship(
        back_populates="illustrations", foreign_keys=[asset_id]
    )

    @property
    def model(self) -> dict:
        return {"url": self.src}
