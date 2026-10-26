import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from gigapoll.data.models import Template
from gigapoll.enums import Modes
from gigapoll.services import poll_service


def make_template(session: Session) -> Template:
    template = Template(
            name='t',
            user_id=1,
            description='d',
            mode=Modes.PLUS_MINUS,
        )
    session.add(template)
    session.flush()
    return template


def test_register_poll_generates_share_token(session: Session) -> None:
    template = make_template(session)

    poll1 = poll_service.resigter_poll(template.id, session)
    poll2 = poll_service.resigter_poll(template.id, session)

    assert poll1.share_token
    assert poll1.share_token != poll2.share_token


def test_get_poll_by_share_token(session: Session) -> None:
    template = make_template(session)
    poll = poll_service.resigter_poll(template.id, session)

    found = poll_service.get_poll_by_share_token(poll.share_token, session)

    assert found.id == poll.id


def test_get_poll_by_unknown_share_token(session: Session) -> None:
    with pytest.raises(NoResultFound):
        poll_service.get_poll_by_share_token('nope', session)
