from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from gigapoll.button import CallbackButton
from gigapoll.data.models import Button
from gigapoll.data.models import Choice
from gigapoll.dto import UserDTO
from gigapoll.dto import UserWithChoiceDTO


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


def get_poll_choices_per_option(
        poll_id: int,
        template_id: int,
        session: Session,
) -> list[CallbackButton]:

    subq = (
            select(Choice.id, Choice.button_id)
            .where(
                Choice.poll_id == poll_id,
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
                Button.id == subq.c.button_id,
            ).group_by(Button.value, Button.id)
            .where(Button.template_id == template_id)
            .subquery()
        )

    return [
            CallbackButton(
                button_name=getattr(r, 'value'),
                button_id=getattr(r, 'id'),
                votes=getattr(r, 'cnt')
            )
            for r
            in session.execute(select(group_subq))
        ]


def get_all_poll_choices(
        poll_id: int,
        session: Session,
) -> list[UserWithChoiceDTO]:
    sql = text(f'''
        select
        user_id
        , last_value(c.first_name) over w first_name
        , last_value(c.last_name) over w last_name
        , last_value(c.username) over w username
        , b.value as value
    from buttons b
    inner join choices c on
        b.id = c.button_id
        and c.poll_id = {poll_id}
    window w as (
        PARTITION by c.user_id
        order by c.cdate DESC
    )
    order by b.id, c.cdate''')

    result = []
    for r in session.execute(sql):
        user_id, first_name, last_name, username, value = tuple(r)
        user = UserDTO(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
        user_with_choice = UserWithChoiceDTO(user=user, choice=str(value))
        result.append(user_with_choice)
    return result


def add_choice(
        user_id: int,
        message_id: int,
        chat_id: int,
        cbdata: str,
        first_name: str,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> Choice:
    c = Choice(
            user_id=user_id,
            message_id=message_id,
            chat_id=chat_id,
            cbdata=cbdata,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
    session.add(c)
    session.commit()
    return c


def add_positive_choice(
        user_id: int,
        first_name: str,
        button_id: int,
        poll_id: int,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> Choice:
    stmt = (
            select(Choice)
            .where(
                Choice.user_id == user_id,
                Choice.poll_id == poll_id,
            )
            .join(Button, Choice.button_id == Button.id)
            .where(Button.is_negative)
        )
    negative = session.scalars(stmt).all()
    if negative:
        delete_stmt = delete(Choice).where(
                Choice.id.in_([c.id for c in negative])
            )
        session.execute(delete_stmt)
    c = Choice(
            user_id=user_id,
            poll_id=poll_id,
            button_id=button_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
    session.add(c)
    session.commit()
    return c


def delete_all_user_choices_from_poll(
        poll_id: int,
        user_id: int,
        session: Session,
) -> None:
    stmt = delete(Choice).where(
            Choice.poll_id == poll_id,
            Choice.user_id == user_id,
        )
    session.execute(stmt)
    session.commit()
