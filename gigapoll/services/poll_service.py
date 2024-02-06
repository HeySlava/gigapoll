from sqlalchemy.orm import Session

from gigapoll.data.models import Poll


def resigter_poll(
        owner_id: int,
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        config: str,
        session: Session,
) -> Poll:
    poll = Poll(
            chat_id=chat_id,
            owner_id=owner_id,
            message_id=message_id,
            message_thread_id=message_thread_id,
            config=config,
        )
    session.add(poll)
    session.commit()
    return poll
