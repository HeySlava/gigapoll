from sqlalchemy.orm import Session

from gigapoll.data.models import Template


def create_template(
        user_id: int,
        template_name: str,
        content: str,
        session: Session,
) -> Template:

    template = session.query(Template).where(
            Template.user_id == user_id,
            Template.name == template_name,
        ).one_or_none()
    if template:
        template.content = content
    else:
        template = Template(
                user_id=user_id,
                content=content,
                name=template_name,
            )
    session.add(template)
    session.commit()
    return template


def get_template(
        user_id: int,
        template_name: str,
        session: Session,
) -> Template:
    return session.query(Template).where(
            Template.user_id == user_id,
            Template.name == template_name,
        ).one()
