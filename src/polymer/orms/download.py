from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .asset import Asset


class Download(Base):
    __tablename__ = "download"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    filename: Mapped[str]

    asset: Mapped["Asset"] = relationship(back_populates="downloads")

    @property
    def path(self) -> Path:
        return Path(self.asset.slug, self.filename)
