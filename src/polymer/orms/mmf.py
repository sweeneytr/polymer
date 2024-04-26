import datetime
from typing import Self, TypeVar

from sqlalchemy import  Select, select
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


T = TypeVar("T")

class Mmf(Base):
    __tablename__ = "mmf"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    access_token: Mapped[str] = mapped_column()
    access_exp: Mapped[datetime.datetime] = mapped_column()
    refresh_token: Mapped[str] = mapped_column()
    refresh_exp: Mapped[datetime.datetime] = mapped_column()

    @property
    def id(self):
        return self.user_id

    @classmethod
    def select_one(cls) -> Select[tuple[Self]]:
        return select(cls)
