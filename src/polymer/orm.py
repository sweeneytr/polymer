from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    creator: Mapped[str]
    details: Mapped[str]
    description: Mapped[str]
    slug: Mapped[str]
    cents: Mapped[int]
    download_url: Mapped[str | None]
    yanked: Mapped[bool]
    downloaded: Mapped[bool]

    @hybrid_property
    def free(self) -> bool:
        return self.cents == 0


class CultsSettings(Base):
    __tablename__ = "cults_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]


engine = create_engine("sqlite:///polymer.db")
Base.metadata.create_all(engine)
