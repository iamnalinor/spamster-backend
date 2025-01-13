import datetime
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import DateTime, Integer, create_engine, func
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    sessionmaker,
)

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
make_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
RawBase: type[Any] = declarative_base()


class Base(RawBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
        nullable=False,
    )


def get_session() -> Iterator[Session]:
    db = make_session()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_session)]
