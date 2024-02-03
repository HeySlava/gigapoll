from pathlib import Path

import data._all_models  # noqa: F401
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import orm


_factory = None


def make_alembic_config(
        base_dir: Path,
) -> Config:
    alembic_path = (base_dir / 'alembic.ini').as_posix()
    config = Config(
            file_=alembic_path,
        )
    migration_dir = 'script_location', (base_dir / 'migrations').as_posix()
    config.set_main_option(migration_dir)

    return config


def global_init(
        base_dir: Path,
        echo: bool,
) -> None:
    global _factory

    if _factory:
        return

    config = make_alembic_config(base_dir)
    conn_str = config.get_main_option('sqlalchemy.url')

    if not conn_str or not conn_str.strip():
        raise Exception('You have to specify conn_str, but your {!r:conn_str}')

    engine = sa.create_engine(
            conn_str, echo=echo, connect_args={'check_same_thread': False})

    _factory = orm.sessionmaker(bind=engine)

    with engine.begin() as connection:
        config.attributes['connection'] = connection
        config.attributes['configure_logger'] = False
        command.upgrade(config, 'head')


def create_session() -> orm.Session:
    global _factory

    if not _factory:
        raise Exception('You must call global_init() before using this method')

    session: orm.Session = _factory()

    try:
        yield session
    finally:
        session.close()
