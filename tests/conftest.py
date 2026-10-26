import os
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault('GIGAPOLL_CONN_STR', 'sqlite:///:memory:')
os.environ.setdefault('POLL_TOKEN', 'test-token')

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from gigapoll.data.models import Base  # noqa: E402


@pytest.fixture
def session(tmp_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
