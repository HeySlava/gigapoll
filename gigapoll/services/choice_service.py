from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy import update
from sqlalchemy.orm import Session

from gigapoll.button import CallbackButton
from gigapoll.data.models import Button
from gigapoll.data.models import Choice
from gigapoll.data.models import Poll
from gigapoll.data.models import Template
from gigapoll.dto import UserDTO
from gigapoll.dto import UserWithChoiceDTO
from gigapoll.enums import Modes


def save_event_participation_choice(
        user_id: int,
        first_name: str,
        button_id: int,
        poll_id: int,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> None:
    """Serialize this mode's read/modify/write on the existing poll row.

    A no-op UPDATE acquires SQLite's write lock (or a DB row lock) before
    reading choices, including when the user has not voted yet.
    """
    try:
        session.execute(update(Poll).where(Poll.id == poll_id).values(
            template_id=Poll.template_id,
        ))
        poll = session.get(Poll, poll_id)
        button = session.get(Button, button_id)
        template = session.get(Template, poll.template_id) if poll else None
        if (not template or template.mode != Modes.EVENT_PARTICIPATION
                or not button or button.template_id != template.id):
            raise ValueError('Invalid event participation button or poll')
        if button.is_positive and button.is_negative:
            raise ValueError('Invalid event participation role')
        rows = session.scalars(select(Choice).where(
            Choice.poll_id == poll_id, Choice.user_id == user_id,
        ).order_by(Choice.id)).all()
        unknown = not button.is_positive and not button.is_negative
        if unknown and len(rows) == 1 and rows[0].button_id == button_id:
            session.commit()
            return
        opposite = None
        for row in rows:
            old_button = session.get(Button, row.button_id)
            if unknown or (not old_button.is_positive
                           and not old_button.is_negative):
                session.delete(row)
            elif opposite is None and (
                (button.is_positive and old_button.is_negative)
                or (button.is_negative and old_button.is_positive)
            ):
                opposite = row
        if opposite is not None:
            session.delete(opposite)
        else:
            session.flush()
            session.add(Choice(
                user_id=user_id, first_name=first_name, last_name=last_name,
                username=username, button_id=button_id, poll_id=poll_id,
            ))
        session.commit()
    except Exception:
        session.rollback()
        raise


def get_event_participation_choices(
        poll_id: int,
        session: Session,
) -> list[UserWithChoiceDTO]:
    rows = session.execute(select(Choice, Button).join(
        Button, Choice.button_id == Button.id,
    ).where(Choice.poll_id == poll_id).order_by(Button.id, Choice.id)).all()
    latest: dict[int, Choice] = {}
    for choice, _ in rows:
        if (choice.user_id not in latest
                or choice.id > latest[choice.user_id].id):
            latest[choice.user_id] = choice
    result = []
    for choice, button in rows:
        user = latest[choice.user_id]
        result.append(UserWithChoiceDTO(
            user=UserDTO(user.user_id, user.first_name, user.last_name,
                         user.username),
            choice=button.value,
        ))
    return result


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


def get_plus_minus_poll_choices(
        poll_id: int,
        session: Session,
) -> list[UserWithChoiceDTO]:
    sql = text('''
WITH cte AS (
    SELECT
        user_id
        , first_name
        , last_name
        , username
        , value
        , is_positive
        , is_negative
        , poll_id
        , cdate
        , button_id
        , ROW_NUMBER() OVER (
            PARTITION BY poll_id, user_id, value ORDER BY cdate
        ) AS rn
        , COALESCE(MAX(rn) FILTER (WHERE is_negative) OVER (
            PARTITION BY poll_id, user_id), 0) AS max_neg
        , COALESCE(MAX(rn) FILTER (WHERE is_positive) OVER (
            PARTITION BY poll_id, user_id), 0) AS max_pos
        FROM (
            SELECT
            user_id
            , last_value(c.first_name) over w first_name
            , last_value(c.last_name) over w last_name
            , last_value(c.username) over w username
            , b.value as value
            , b.is_positive
            , b.is_negative
            , ROW_NUMBER() OVER (
                PARTITION BY poll_id, user_id, value ORDER BY c.cdate
            ) AS rn
            , poll_id
            , c.cdate
            , c.button_id
            FROM choices c
            inner join buttons b on c.button_id = b.id
            where c.poll_id=:poll_id
            window w as (
                PARTITION by c.poll_id, c.user_id
                order by c.cdate DESC
            )
        ) t
    )
    select
        user_id
        , first_name
        , last_name
        , username
        , value
    from (
        SELECT
            user_id
            , first_name
            , last_name
            , username
            , value
            , cdate
            , button_id
        FROM cte
        WHERE is_positive AND rn > max_neg AND max_pos - max_neg > 0
        UNION ALL
        SELECT
            user_id
            , first_name
            , last_name
            , username
            , value
            , cdate
            , button_id
        FROM cte
        WHERE is_negative AND rn > max_pos AND max_neg - max_pos > 0
    ) t
    order by button_id, cdate;
''')

    sql = sql.bindparams(poll_id=poll_id)

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


def toggle_choice(
        user_id: int,
        first_name: str,
        button_id: int,
        poll_id: int,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> None:
    stmt = select(Choice).where(
            Choice.poll_id == poll_id,
            Choice.user_id == user_id,
            Choice.button_id == button_id,
        )
    existing = session.scalars(stmt).all()
    if existing:
        delete_stmt = delete(Choice).where(
                Choice.id.in_([c.id for c in existing])
            )
        session.execute(delete_stmt)
        session.commit()
        return
    add_choice(
            user_id=user_id,
            first_name=first_name,
            button_id=button_id,
            poll_id=poll_id,
            last_name=last_name,
            username=username,
            session=session,
        )


def get_user_button_choices(
        poll_id: int,
        user_id: int,
        session: Session,
) -> set[int]:
    stmt = select(Choice.button_id).where(
            Choice.poll_id == poll_id,
            Choice.user_id == user_id,
        )
    return set(session.scalars(stmt).all())


def add_choice(
        user_id: int,
        first_name: str,
        button_id: int,
        poll_id: int,
        last_name: str | None,
        username: str | None,
        session: Session,
) -> Choice:
    c = Choice(
            user_id=user_id,
            button_id=button_id,
            poll_id=poll_id,
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


def get_last_user_choice_for_poll(
        poll_id: int,
        user_id: int,
        session: Session,
) -> Choice | None:
    stmt = select(Choice).where(
            Choice.poll_id == poll_id,
            Choice.user_id == user_id,
        ).order_by(Choice.cdate.desc()).limit(1)
    return session.scalars(stmt).one_or_none()


def delete_choice(
        choice: Choice,
        session: Session,
) -> None:
    session.delete(choice)
    session.commit()


def get_number_of_choice(
        poll_id: int,
        session: Session,
) -> int:
    return session.query(func.count(Choice.id)).filter(
        Choice.poll_id == poll_id,
        Choice.cdate >= func.datetime('now', '-1 minute')
    ).scalar()
