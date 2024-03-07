from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from gigapoll.button import CallbackButton
from gigapoll.data.models import Button
from gigapoll.data.models import Poll
from gigapoll.data.models import Template


def create_template(
        user_id: int,
        template_name: str,
        description: str,
        mode: str,
        session: Session,
        version: int = 1,
) -> Template:
    template = Template(
            user_id=user_id,
            name=template_name,
            version=version,
            description=description,
            mode=mode
        )
    session.add(template)
    session.commit()
    return template


def get_template_by_name(
        user_id: int,
        template_name: str,
        session: Session,
) -> Template:
    return session.query(Template).where(
            Template.user_id == user_id,
            Template.name == template_name,
        ).one()


def get_template_by_id(
        user_id: int,
        template_id: int,
        session: Session,
) -> Template:
    return session.query(Template).where(
            Template.user_id == user_id,
            Template.id == template_id,
        ).one()


def get_buttons_for_empty_poll(
        template_id: int,
        session: Session,
) -> list[CallbackButton]:
    query_result = (
            session.query(
                Template.name,
                Button.value,
                Button.id,
            )
            .where(
                Template.id == template_id,
            )
            .join(Button, Template.id == Button.template_id)
            .all()
        )

    result = []
    for row in query_result:
        _, choice_name, id = row
        result.append(
                CallbackButton(
                    button_name=choice_name,
                    button_id=id,
                    votes=0,
                )
            )
    return result


def get_template_by_poll_id(
        poll_id: int,
        session: Session,
) -> Template:
    stmt = (
            select(Template)
            .join(Poll)
            .where(Poll.id == poll_id)
        )
    return session.scalars(stmt).one()


def get_all_templates_for_user(
        user_id: int,
        session: Session,
) -> Sequence[Template]:
    stmt = select(Template).where(Template.user_id == user_id)
    return session.scalars(stmt).all()
