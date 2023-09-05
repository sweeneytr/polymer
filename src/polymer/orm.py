from pathlib import Path

from sqlalchemy import (Boolean, Column, ColumnElement, ForeignKey, Table,
                        create_engine, type_coerce)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


tag_association_table = Table(
    "tag_association_table",
    Base.metadata,
    Column("asset_id", ForeignKey("asset.id")),
    Column("tag_id", ForeignKey("tag.id")),
)


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

    downloads: Mapped[list["Download"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    tags: Mapped[list["Tag"]] = relationship(
        back_populates="assets", secondary=tag_association_table
    )

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


class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str]

    assets: Mapped[list[Asset]] = relationship(
        back_populates="tags", secondary=tag_association_table
    )


class Download(Base):
    __tablename__ = "download"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("asset.id"))
    filename: Mapped[str]

    asset: Mapped[Asset] = relationship(back_populates="downloads")

    @property
    def path(self) -> Path:
        return Path(self.asset.slug, self.filename)


class CultsSettings(Base):
    __tablename__ = "cults_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]


engine = create_engine("sqlite:///polymer.db")
Base.metadata.create_all(engine)
