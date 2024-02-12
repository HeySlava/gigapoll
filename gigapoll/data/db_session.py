import os
from typing import Generator

import sqlalchemy as sa
from sqlalchemy import orm


_factory = None


conn_str = os.environ['GIGAPOLL_CONN_STR']


def global_init(
        echo: bool = False,
        conn_str: str = conn_str,
) -> sa.Engine:
    global _factory

    if _factory:
        return _factory

    if not conn_str or not conn_str.strip():
        raise Exception('You have to specify conn_str, but your {!r:conn_str}')

    engine = sa.create_engine(
            conn_str, echo=echo,
            connect_args={'check_same_thread': False},
        )

    _factory = orm.sessionmaker(bind=engine)

    return engine


def create_session() -> Generator[orm.Session, None, None]:
    global _factory

    if not _factory:
        raise Exception('You must call global_init() before using this method')

    session: orm.Session = _factory()

    try:
        yield session
    finally:
        session.close()
