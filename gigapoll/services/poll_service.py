import secrets

from sqlalchemy.orm import Session

from gigapoll.data.models import Poll


def resigter_poll(
        template_id: int,
        session: Session,
) -> Poll:
    poll = Poll(
            template_id=template_id,
            share_token=secrets.token_urlsafe(16),
        )
    session.add(poll)
    session.commit()
    return poll


def get_poll_by_id(
        poll_id: int,
        session: Session,
) -> Poll:
    return session.query(Poll).where(Poll.id == poll_id).one()


def get_poll_by_share_token(
        share_token: str,
        session: Session,
) -> Poll:
    return session.query(Poll).where(
            Poll.share_token == share_token,
        ).one()


def get_poll(
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        session: Session,
) -> Poll:
    return session.query(Poll).where(
            Poll.chat_id == chat_id,
            Poll.message_id == message_id,
            Poll.message_thread_id == message_thread_id,
        ).one()
