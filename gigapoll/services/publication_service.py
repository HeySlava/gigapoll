from sqlalchemy.orm import Session

from gigapoll.data.models import Publication


def register_publication(
        poll_id: int,
        inline_message_id: str,
        session: Session,
) -> None:
    exists = session.query(Publication).where(
            Publication.inline_message_id == inline_message_id,
        ).first()
    if exists:
        return
    session.add(
            Publication(
                poll_id=poll_id,
                inline_message_id=inline_message_id,
            )
        )
    session.commit()


def get_poll_publications(
        poll_id: int,
        session: Session,
) -> list[Publication]:
    return session.query(Publication).where(
            Publication.poll_id == poll_id,
        ).all()


def delete_publication(
        inline_message_id: str,
        session: Session,
) -> None:
    session.query(Publication).where(
            Publication.inline_message_id == inline_message_id,
        ).delete()
    session.commit()
