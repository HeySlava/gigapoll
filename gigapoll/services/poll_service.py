from sqlalchemy.orm import Session

from gigapoll.data.models import Poll


def resigter_poll(
        template_id: int,
        session: Session,
) -> Poll:
    poll = Poll(
            template_id=template_id,
        )
    session.add(poll)
    session.commit()
    return poll


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
