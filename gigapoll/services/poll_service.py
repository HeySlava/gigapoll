from sqlalchemy.orm import Session

from gigapoll.data.models import Poll


def resigter_poll(
        owner_id: int,
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        template_name: str,
        session: Session,
) -> Poll:
    poll = Poll(
            chat_id=chat_id,
            owner_id=owner_id,
            message_id=message_id,
            message_thread_id=message_thread_id,
            template_name=template_name,
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
