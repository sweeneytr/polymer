from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


tag_association_table = Table(
    "tag_association_table",
    Base.metadata,
    Column("asset_id", ForeignKey("asset.id")),
    Column("tag_id", ForeignKey("tag.id")),
)


engine = create_engine("sqlite:///polymer.db")
Base.metadata.create_all(engine)
