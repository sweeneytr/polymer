from select import select
from typing import Any, Iterable, Protocol, TypeVar

from sqlalchemy import Select, func
from sqlalchemy.orm import Session

T = TypeVar("T")


class Pagination(Protocol):
    offset: int
    limit: int


class DbProxy:
    def __init__(self, session: Session) -> None:
        self.session = session

    def count(self, stmt: Select) -> int:
        return self.session.execute(select(func.count()).select_from(stmt)).scalar_one()

    def all_or_paginated(
        self, stmt: Select[tuple[T]], pagination: Pagination | None
    ) -> Iterable[T]:
        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)

        return self.session.execute(stmt).scalars().all()

    def one(self, stmt: Select[tuple[T]]) -> T:
        return self.session.execute(stmt).scalar_one()

    def add(self, orm: Any) -> None:
        return self.session.add(orm)

    def delete(self, orm: Any) -> None:
        return self.session.delete(orm)

    def commit(self) -> None:
        return self.session.commit()
