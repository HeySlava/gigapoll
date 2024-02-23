from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from gigapoll.data.models import Button
from gigapoll.data.models import Choice
from gigapoll.dto import CntPerValue
from gigapoll.dto import UserChoiceDTO


def get_poll_choices_models(
        user_id: int,
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        session: Session,
) -> list[Choice]:
    return session.query(Choice).where(
            Choice.user_id == user_id,
            Choice.message_id == message_id,
            Choice.message_thread_id == message_thread_id,
            Choice.chat_id == chat_id,
        ).all()


def get_poll_choices(
        user_id: int,
        message_id: int,
        chat_id: int,
        message_thread_id: int | None,
        session: Session,
) -> dict[str, int]:

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


def get_poll_choices_per_option(
        message_id: int,
        chat_id: int,
        session: Session,
) -> list[CntPerValue]:

    subq = (
            select(Choice.id, Choice.cbdata)
            .where(
                Choice.message_id == message_id,
                Choice.chat_id == chat_id,
            )
            .subquery('choices')
        )

    group_subq = (
            select(
                Button.value,
                Button.id,
                func.count(subq.c.id).label('cnt'),
            ).outerjoin(
                subq,
                Button.id == subq.c.cbdata
            ).group_by(Button.value, Button.id)
            .subquery()
        )

    return [
            CntPerValue(
                button_name=getattr(r, 'value'),
                button_cbdata=getattr(r, 'id'),
                cnt=getattr(r, 'cnt')
            )
            for r
            in session.execute(select(group_subq))
        ]


def get_all_poll_choices(
        message_id: int,
        chat_id: int,
        session: Session,
) -> list[UserChoiceDTO]:
    from sqlalchemy import text
    sql = text(f'''
        select
        last_value(c.first_name) over w first_name
        , last_value(c.last_name) over w last_name
        , last_value(c.username) over w username
        , b.value as value
    from buttons b
    inner join choices c on
        b.id = c.cbdata
        and c.message_id = {message_id}
        and c.chat_id = {chat_id}
    window w as (
        PARTITION by c.user_id
        order by c.cdate DESC
    )
    order by c.cdate''')

    sql = sql.columns(
            Choice.first_name,
            Choice.last_name,
            Choice.username,
            Button.value,
        )

    return [UserChoiceDTO(*tuple(r)) for r in session.execute(sql)]


def add_choice(
        user_id: int,
        message_id: int,
        chat_id: int,
        # message_thread_id: int | None,
        cbdata: str,
        first_name: str,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> Choice:
    c = Choice(
            user_id=user_id,
            message_id=message_id,
            # message_thread_id=message_thread_id,
            chat_id=chat_id,
            cbdata=cbdata,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
    session.add(c)
    session.commit()
    return c
