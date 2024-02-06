from sqlalchemy.orm import Session

from gigapoll.data.models import Choice


def get_poll_choices(
        user_id: int,
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        session: Session,
) -> dict[str, int]:

    from sqlalchemy import select
    from sqlalchemy import func
    subq = (
            select(
                Choice.choice,
                func.count(Choice.choice).label('cnt'),
            )
            .where(
                Choice.user_id == user_id,
                Choice.message_id == message_id,
                Choice.message_thread_id == message_thread_id,
                Choice.chat_id == chat_id,
            )
            .group_by(Choice.choice)
            .subquery()
        )

    return {
            getattr(r, 'choice'): getattr(r, 'cnt') for
            r in
            session.execute(select(subq))
        }


def add_choice(
        user_id: int,
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        choice: str,
        first_name: str,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> Choice:
    c = Choice(
            user_id=user_id,
            message_id=message_id,
            message_thread_id=message_thread_id,
            chat_id=chat_id,
            choice=choice,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
    session.add(c)
    session.commit()
    return c
