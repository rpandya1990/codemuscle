from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from codemuscle.config import Settings, get_settings


def create_engine_from_settings(settings: Settings) -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
    return create_engine_from_settings(get_settings())


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
