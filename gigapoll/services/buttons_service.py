from sqlalchemy import delete
from sqlalchemy.orm import Session

from gigapoll.data.models import Button


def add_choices(
        template_choices: list[Button],
        session: Session,
) -> None:
    stmt = delete(Button).where(
            Button.template_id == template_choices[0].template_id,
        )
    session.execute(stmt)
    session.commit()
    session.add_all(template_choices)
    session.commit()
