from sqlalchemy.orm import Session

from gigapoll.data.models import Button
from gigapoll.data.models import Poll
from gigapoll.data.models import Template
from gigapoll.enums import Modes
from gigapoll.services import choice_service


def make_poll(
        session: Session,
        n_options: int = 3,
) -> tuple[Poll, list[Button]]:
    template = Template(
            name='multi',
            user_id=1,
            description='desc',
            mode=Modes.MULTI_SELECT,
        )
    session.add(template)
    session.flush()
    buttons = [
            Button(template_id=template.id, value=f'opt{i}')
            for i in range(n_options)
        ]
    session.add_all(buttons)
    session.flush()
    poll = Poll(template_id=template.id)
    session.add(poll)
    session.commit()
    return poll, buttons


def toggle(
        session: Session,
        poll_id: int,
        button_id: int,
        user_id: int,
) -> None:
    choice_service.toggle_choice(
            user_id=user_id,
            first_name=f'user{user_id}',
            last_name=None,
            username=None,
            button_id=button_id,
            poll_id=poll_id,
            session=session,
        )


def selected(session: Session, poll_id: int, user_id: int) -> set[int]:
    return choice_service.get_user_button_choices(
            poll_id=poll_id,
            user_id=user_id,
            session=session,
        )


def votes_per_button(
        session: Session,
        poll: Poll,
) -> dict[int, int]:
    buttons = choice_service.get_poll_choices_per_option(
            poll_id=poll.id,
            template_id=poll.template_id,
            session=session,
        )
    return {b.button_id: b.votes for b in buttons}


def test_toggle_selects_option(session: Session) -> None:
    poll, buttons = make_poll(session)

    toggle(session, poll.id, buttons[0].id, user_id=100)

    assert selected(session, poll.id, user_id=100) == {buttons[0].id}


def test_toggle_deselects_option(session: Session) -> None:
    poll, buttons = make_poll(session)

    toggle(session, poll.id, buttons[0].id, user_id=100)
    toggle(session, poll.id, buttons[0].id, user_id=100)

    assert selected(session, poll.id, user_id=100) == set()


def test_user_can_select_all_options(session: Session) -> None:
    poll, buttons = make_poll(session)

    for b in buttons:
        toggle(session, poll.id, b.id, user_id=100)

    assert selected(session, poll.id, user_id=100) == {
            b.id for b in buttons
        }
    assert votes_per_button(session, poll) == {
            b.id: 1 for b in buttons
        }


def test_user_can_deselect_all_options(session: Session) -> None:
    poll, buttons = make_poll(session)

    for b in buttons:
        toggle(session, poll.id, b.id, user_id=100)
    for b in buttons:
        toggle(session, poll.id, b.id, user_id=100)

    assert selected(session, poll.id, user_id=100) == set()
    assert votes_per_button(session, poll) == {
            b.id: 0 for b in buttons
        }


def test_choices_are_independent_between_users(session: Session) -> None:
    poll, buttons = make_poll(session)
    b0, b1, b2 = buttons

    toggle(session, poll.id, b0.id, user_id=100)
    toggle(session, poll.id, b1.id, user_id=100)
    toggle(session, poll.id, b1.id, user_id=200)
    toggle(session, poll.id, b2.id, user_id=200)

    toggle(session, poll.id, b1.id, user_id=100)

    assert selected(session, poll.id, user_id=100) == {b0.id}
    assert selected(session, poll.id, user_id=200) == {b1.id, b2.id}
    assert votes_per_button(session, poll) == {
            b0.id: 1,
            b1.id: 1,
            b2.id: 1,
        }


def test_toggles_do_not_affect_other_polls(session: Session) -> None:
    poll, buttons = make_poll(session)
    other_poll, _ = make_poll(session)

    toggle(session, poll.id, buttons[0].id, user_id=100)

    assert selected(session, other_poll.id, user_id=100) == set()
