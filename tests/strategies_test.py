import asyncio

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.orm import Session

from gigapoll.data.models import Button
from gigapoll.data.models import Template
from gigapoll.enums import Modes
from gigapoll.exc import StrategyFinishedError
from gigapoll.template_creation.strategies import MultiSelectStrategy


def make_state() -> FSMContext:
    return FSMContext(
            storage=MemoryStorage(),
            key=StorageKey(bot_id=1, chat_id=1, user_id=1),
        )


def test_full_creation_flow_saves_template(session: Session) -> None:
    async def run() -> None:
        state = make_state()
        await state.update_data(mode=Modes.MULTI_SELECT)
        strategy = MultiSelectStrategy(state)

        await strategy.process_answer('my template')
        await strategy.process_answer('my description')
        await strategy.process_answer('opt1\nopt2\nopt3')

        with pytest.raises(StrategyFinishedError):
            await strategy.get_next_question()

        await strategy.save_template(user_id=1, session=session)

    asyncio.run(run())

    template = session.query(Template).filter_by(name='my template').one()
    assert template.mode == Modes.MULTI_SELECT
    assert template.description == 'my description'
    values = {
            b.value for b
            in session.query(Button).filter_by(template_id=template.id)
        }
    assert values == {'opt1', 'opt2', 'opt3'}


def test_too_few_options_are_rejected() -> None:
    async def run() -> None:
        strategy = MultiSelectStrategy(make_state())
        strategy.step = 2

        with pytest.raises(ValueError, match='минимум'):
            await strategy.process_answer('only one option')

    asyncio.run(run())


def test_too_many_options_are_rejected() -> None:
    async def run() -> None:
        strategy = MultiSelectStrategy(make_state())
        strategy.step = 2
        options = '\n'.join(f'opt{i}' for i in range(11))

        with pytest.raises(ValueError, match='максимум'):
            await strategy.process_answer(options)

    asyncio.run(run())


def test_min_options_boundary_is_allowed() -> None:
    async def run() -> None:
        state = make_state()
        strategy = MultiSelectStrategy(state)
        strategy.step = 2

        await strategy.process_answer('opt1\nopt2')

        data = await state.get_data()
        assert data['options'] == ['opt1', 'opt2']

    asyncio.run(run())


def test_max_options_boundary_is_allowed() -> None:
    async def run() -> None:
        state = make_state()
        strategy = MultiSelectStrategy(state)
        strategy.step = 2
        options = '\n'.join(f'opt{i}' for i in range(10))

        await strategy.process_answer(options)

        data = await state.get_data()
        assert len(data['options']) == 10

    asyncio.run(run())


def test_blank_lines_are_ignored() -> None:
    async def run() -> None:
        state = make_state()
        strategy = MultiSelectStrategy(state)
        strategy.step = 2

        await strategy.process_answer('opt1\n\n   \nopt2\n')

        data = await state.get_data()
        assert data['options'] == ['opt1', 'opt2']

    asyncio.run(run())


def test_failed_validation_does_not_advance_step() -> None:
    async def run() -> None:
        strategy = MultiSelectStrategy(make_state())
        strategy.step = 2

        with pytest.raises(ValueError):
            await strategy.process_answer('only one option')

        assert strategy.step == 2

    asyncio.run(run())
