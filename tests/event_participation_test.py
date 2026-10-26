import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from strategies_test import make_state

from gigapoll import kb
from gigapoll.data.models import Button
from gigapoll.data.models import Poll
from gigapoll.data.models import Template
from gigapoll.enums import Modes
from gigapoll.services import choice_service
from gigapoll.template_creation.strategies import STRATEGY_REGISTRY


def create_event(
    session: Session,
    labels: tuple[str, ...] = ('Буду', 'Не буду', 'Пока не знаю'),
) -> tuple[int, list[int]]:
    async def run() -> None:
        state = make_state()
        await state.update_data(mode=Modes.EVENT_PARTICIPATION)
        strategy = STRATEGY_REGISTRY[Modes.EVENT_PARTICIPATION](state)
        await strategy.process_answer('event template')
        await strategy.process_answer('Event description')
        for i, label in enumerate(labels):
            question = await strategy.get_next_question()
            assert f'Кнопка {i + 1}' in question
            await strategy.process_answer(label)
        await strategy.save_template(1, session)

    asyncio.run(run())
    template = session.scalars(
        select(Template).order_by(Template.id.desc())
    ).first()
    buttons = session.scalars(
        select(Button)
        .where(Button.template_id == template.id)
        .order_by(Button.id)
    ).all()
    poll = Poll(template_id=template.id)
    session.add(poll)
    session.commit()
    return poll.id, [b.id for b in buttons]


def vote(session: Session, poll: int, button: int, user: int = 100) -> None:
    choice_service.save_event_participation_choice(
        user_id=user,
        first_name=f'user{user}',
        last_name=None,
        username=None,
        poll_id=poll,
        button_id=button,
        session=session,
    )


@pytest.mark.parametrize(
    ('sequence', 'label', 'count'),
    [
        ([0, 0, 0], 'Буду', 3),
        ([0, 0, 0, 1], 'Буду', 2),
        ([0, 0, 0, 1, 2], 'Пока не знаю', 1),
        ([0, 0, 2, 0], 'Буду', 1),
        ([0, 1], None, 0),
        ([1, 1, 0], 'Не буду', 1),
        ([1, 1, 2, 2], 'Пока не знаю', 1),
        ([2, 1], 'Не буду', 1),
        ([0] * 30 + [1] * 12, 'Буду', 18),
    ],
)
def test_transitions_persist(
    session: Session,
    sequence: list[int],
    label: str | None,
    count: int,
) -> None:
    poll, ids = create_event(session)
    for index in sequence:
        vote(session, poll, ids[index])
    with Session(session.bind) as fresh:
        choices = choice_service.get_event_participation_choices(poll, fresh)
        assert len(choices) == count
        assert {c.choice for c in choices} == ({label} if count else set())
        assert {c.user.user_id for c in choices} <= {100}


def test_callback_dispatch_and_render(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib
    from unittest.mock import AsyncMock

    from aiogram.types import Update
    from sqlalchemy.orm import sessionmaker

    # Syntactically valid, deliberately fake test token; no network calls.
    monkeypatch.setenv('POLL_TOKEN', '123456:TEST_ONLY_NOT_A_REAL_BOT_TOKEN')
    monkeypatch.setenv('GIGAPOLL_CONN_STR', 'sqlite://')
    main = importlib.import_module('gigapoll.main')
    monkeypatch.setattr(
        main.db_session, '_factory', sessionmaker(session.bind)
    )
    transport = AsyncMock(return_value=True)
    monkeypatch.setattr(main.bot.session, 'make_request', transport)
    poll, ids = create_event(session)

    async def run() -> None:
        for i, index in enumerate([0, 0, 0, 1, 2, 2, 0]):
            update = Update.model_validate(
                {
                    'update_id': i,
                    'callback_query': {
                        'id': str(i),
                        'chat_instance': 'test',
                        'inline_message_id': 'inline-test',
                        'from': {
                            'id': 100,
                            'is_bot': False,
                            'first_name': 'user100',
                        },
                        'data': f'vote:{ids[index]}:{poll}',
                    },
                }
            )
            await main.dp.feed_update(main.bot, update)
        from gigapoll.states import CreateTemplate
        from gigapoll.template_creation import strategies

        state = main.dp.fsm.get_context(
            bot=main.bot,
            chat_id=100,
            user_id=100,
        )
        strategy = strategies.EventParticipationStrategy(state)
        await state.update_data(strategy=strategy)
        await state.set_state(CreateTemplate.processing_creation)
        for action in ['back', 'cancel']:
            if action == 'cancel':
                await state.set_state(CreateTemplate.processing_creation)
            update = Update.model_validate(
                {
                    'update_id': 100,
                    'callback_query': {
                        'id': action,
                        'chat_instance': 'test',
                        'from': {
                            'id': 100,
                            'is_bot': False,
                            'first_name': 'user',
                        },
                        'data': f'creation:{action}',
                        'message': {
                            'message_id': 1,
                            'date': 1,
                            'chat': {'id': 100, 'type': 'private'},
                            'text': 'wizard',
                        },
                    },
                }
            )
            await main.dp.feed_update(main.bot, update)
            expected = (
                CreateTemplate.selecting_mode.state
                if action == 'back'
                else None
            )
            assert await state.get_state() == expected
        assert await state.get_data() == {}

    asyncio.run(run())
    edits = [
        call.args[1]
        for call in transport.call_args_list
        if call.args[1].__api_method__ == 'editMessageText'
        and call.args[1].inline_message_id == 'inline-test'
    ]
    assert len(edits) == 7
    assert 'Буду</b> (3 votes)' in edits[2].text
    assert '(+2)' in edits[2].text
    assert 'Пока не знаю</b> (1 vote)' in edits[4].text
    assert 'Буду</b>' not in edits[4].text
    assert 'Буду</b> (1 vote)' in edits[-1].text
    assert len(edits[-1].reply_markup.inline_keyboard) == 3


@pytest.mark.parametrize('bad', ['', '   ', ' YES '])
def test_invalid_labels_do_not_advance(bad: str) -> None:
    async def run() -> None:
        from gigapoll.template_creation import strategies

        state = make_state()
        strategy = strategies.EventParticipationStrategy(state)
        strategy.step = 2
        await strategy.process_answer('Yes')
        with pytest.raises(ValueError):
            await strategy.process_answer(bad)
        assert strategy.step == 3

    asyncio.run(run())


def test_defaults_and_back(session: Session) -> None:
    async def run() -> None:
        from gigapoll.exc import StrategyFinishedError
        from gigapoll.template_creation import strategies

        state = make_state()
        strategy = strategies.EventParticipationStrategy(state)
        assert not await strategy.go_back()
        await strategy.process_answer('event')
        await strategy.process_answer('desc')
        for _ in range(3):
            await strategy.process_answer('По умолчанию')
        with pytest.raises(StrategyFinishedError):
            await strategy.get_next_question()
        assert await strategy.go_back()
        assert (
            'Кнопка 3 — Я пока не знаю' in await strategy.get_next_question()
        )
        await strategy.process_answer('Maybe')
        await strategy.save_template(1, session)
        assert [
            b.value
            for b in session.scalars(select(Button).order_by(Button.id))
        ] == ['Я буду участвовать', 'Я не буду участвовать', 'Maybe']

    asyncio.run(run())


def test_isolation_and_invalid_buttons(session: Session) -> None:
    poll, ids = create_event(session)
    other, other_ids = create_event(session)
    vote(session, poll, ids[0])
    vote(session, poll, ids[0], user=200)
    vote(session, other, other_ids[1])
    broken = Button(
        template_id=session.get(Poll, poll).template_id,
        value='broken',
        is_positive=True,
        is_negative=True,
    )
    session.add(broken)
    session.commit()
    for button in [other_ids[2], 999999, broken.id]:
        with pytest.raises(ValueError):
            vote(session, poll, button)
        assert (
            len(choice_service.get_event_participation_choices(poll, session))
            == 2
        )
    with pytest.raises(ValueError):
        vote(session, 999999, ids[0])
    vote(session, poll, ids[2])
    assert {
        (c.user.user_id, c.choice)
        for c in choice_service.get_event_participation_choices(poll, session)
    } == {(100, 'Пока не знаю'), (200, 'Буду')}
    assert [
        c.choice
        for c in choice_service.get_event_participation_choices(other, session)
    ] == ['Не буду']


def test_insert_failure_rolls_back_reset(session: Session) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    poll, ids = create_event(session)
    vote(session, poll, ids[0])
    vote(session, poll, ids[0])
    session.execute(
        text(f'''CREATE TRIGGER reject_unknown BEFORE INSERT ON choices
        WHEN NEW.button_id = {ids[2]}
        BEGIN
            SELECT CASE WHEN EXISTS (
                SELECT 1 FROM choices
                WHERE poll_id = NEW.poll_id AND user_id = NEW.user_id
            ) THEN RAISE(ABORT, 'reset not flushed')
            ELSE RAISE(ABORT, 'test insert failure') END;
        END''')
    )
    session.commit()
    with pytest.raises(IntegrityError, match='test insert failure'):
        vote(session, poll, ids[2])
    with Session(session.bind) as fresh:
        assert [
            c.choice
            for c in choice_service.get_event_participation_choices(
                poll, fresh
            )
        ] == ['Буду', 'Буду']


@pytest.mark.parametrize('pair', [(0, 0), (0, 1), (2, 2), (0, 2), (1, 2)])
def test_two_session_race(session: Session, pair: tuple[int, int]) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    poll, ids = create_event(session)
    engine = session.bind
    barrier = Barrier(2)

    def worker(index: int) -> None:
        with Session(engine) as independent:
            barrier.wait(timeout=5)
            vote(independent, poll, ids[index])

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, pair))
    with Session(engine) as fresh:
        rows = choice_service.get_event_participation_choices(poll, fresh)
        labels = [c.choice for c in rows]
        print(f'two-session SQLite race {pair}: {labels!r}')
        if pair == (0, 0):
            assert labels == ['Буду', 'Буду']
        elif pair == (0, 1):
            assert labels == []
        elif pair == (2, 2):
            assert labels == ['Пока не знаю']
        else:
            assert labels in [
                ['Пока не знаю'],
                ['Буду' if pair[0] == 0 else 'Не буду'],
            ]


def test_old_plus_minus_arithmetic_unchanged(session: Session) -> None:
    poll, ids = create_event(session)
    template = session.get(Template, session.get(Poll, poll).template_id)
    template.mode = Modes.PLUS_MINUS
    session.commit()
    for index in [1, 1, 0]:
        choice_service.add_choice(
            user_id=100,
            first_name='user',
            last_name=None,
            username=None,
            button_id=ids[index],
            poll_id=poll,
            session=session,
        )
    assert [
        c.choice
        for c in choice_service.get_plus_minus_poll_choices(poll, session)
    ] == ['Не буду']
    with pytest.raises(ValueError):
        vote(session, poll, ids[2])


def test_creation(session: Session) -> None:
    poll, ids = create_event(session, (' Yes ', ' No ', ' Maybe '))
    buttons = [session.get(Button, i) for i in ids]
    assert [b.value for b in buttons] == ['Yes', 'No', 'Maybe']
    assert [(b.is_positive, b.is_negative) for b in buttons] == [
        (True, None),
        (None, True),
        (None, None),
    ]
    assert any(
        b.callback_data == '3'
        for row in kb.get_different_modes_kb().inline_keyboard
        for b in row
    )
