from sqlalchemy.orm import Session

from gigapoll.data.models import Poll
from gigapoll.data.models import Publication
from gigapoll.data.models import Template
from gigapoll.enums import Modes
from gigapoll.services import publication_service


def make_poll(session: Session) -> Poll:
    template = Template(
            name='t',
            user_id=1,
            description='d',
            mode=Modes.PLUS_MINUS,
        )
    session.add(template)
    session.flush()
    poll = Poll(template_id=template.id)
    session.add(poll)
    session.commit()
    return poll


def test_register_publication(session: Session) -> None:
    poll = make_poll(session)

    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )

    publications = publication_service.get_poll_publications(
            poll_id=poll.id,
            session=session,
        )
    assert [p.inline_message_id for p in publications] == ['imid-1']


def test_register_publication_is_idempotent(session: Session) -> None:
    poll = make_poll(session)

    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )
    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )

    assert session.query(Publication).count() == 1


def test_get_poll_publications_filters_by_poll(session: Session) -> None:
    poll = make_poll(session)
    other_poll = make_poll(session)

    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )
    publication_service.register_publication(
            poll_id=other_poll.id,
            inline_message_id='imid-2',
            session=session,
        )

    publications = publication_service.get_poll_publications(
            poll_id=poll.id,
            session=session,
        )
    assert [p.inline_message_id for p in publications] == ['imid-1']


def test_delete_publication(session: Session) -> None:
    poll = make_poll(session)
    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )

    publication_service.delete_publication(
            inline_message_id='imid-1',
            session=session,
        )

    assert session.query(Publication).count() == 0
