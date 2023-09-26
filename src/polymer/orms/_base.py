from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.orm import DeclarativeBase

from ..config import settings


class Base(DeclarativeBase):
    pass


tag_association_table = Table(
    "tag_association_table",
    Base.metadata,
    Column("asset_id", ForeignKey("asset.id")),
    Column("tag_id", ForeignKey("tag.id")),
)


engine = create_engine(settings.db_url)
