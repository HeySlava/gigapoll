import asyncio
from typing import Any

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import EditMessageText
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.orm import Session

from gigapoll import publication_updater
from gigapoll.data.models import Poll
from gigapoll.data.models import Publication
from gigapoll.data.models import Template
from gigapoll.enums import Modes
from gigapoll.services import publication_service
from gigapoll.utils import CallbackReply


class FakeBot:

    def __init__(self, errors: dict[str, list[Exception]] | None = None):
        self.calls: list[dict[str, Any]] = []
        self.errors = errors or {}

    async def edit_message_text(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        imid = kwargs['inline_message_id']
        if self.errors.get(imid):
            raise self.errors[imid].pop(0)


def render(poll_id: int, session: Session) -> CallbackReply:
    return CallbackReply(
            text=f'poll {poll_id} text',
            markup=InlineKeyboardMarkup(inline_keyboard=[]),
        )


def make_poll(session: Session) -> Poll:
    template = Template(
            name='t',
            user_id=1,
            description='d',
            mode=Modes.PLUS_MINUS,
        )
    session.add(template)
    session.flush()
    poll = Poll(template_id=template.id)
    session.add(poll)
    session.commit()
    return poll


def bad_request(message: str) -> TelegramBadRequest:
    method = EditMessageText(inline_message_id='x', text='t')
    return TelegramBadRequest(method=method, message=message)


@pytest.fixture(autouse=True)
def clean_queue() -> Any:
    publication_updater._pending_polls.clear()
    while not publication_updater._update_queue.empty():
        publication_updater._update_queue.get_nowait()
    yield


def test_update_publications_edits_each_publication(session: Session) -> None:
    poll = make_poll(session)
    for imid in ('imid-1', 'imid-2'):
        publication_service.register_publication(
                poll_id=poll.id,
                inline_message_id=imid,
                session=session,
            )
    bot = FakeBot()

    asyncio.run(publication_updater.update_publications(
            bot=bot,
            poll_id=poll.id,
            render=render,
            session=session,
            pacing=0,
        ))

    edited = {c['inline_message_id'] for c in bot.calls}
    assert edited == {'imid-1', 'imid-2'}
    assert all(c['text'] == f'poll {poll.id} text' for c in bot.calls)


def test_not_modified_error_is_suppressed(session: Session) -> None:
    poll = make_poll(session)
    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )
    bot = FakeBot(errors={
            'imid-1': [bad_request('message is not modified')],
        })

    asyncio.run(publication_updater.update_publications(
            bot=bot,
            poll_id=poll.id,
            render=render,
            session=session,
            pacing=0,
        ))

    assert session.query(Publication).count() == 1


def test_deleted_message_removes_publication(session: Session) -> None:
    poll = make_poll(session)
    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )
    bot = FakeBot(errors={
            'imid-1': [bad_request('message to edit not found')],
        })

    asyncio.run(publication_updater.update_publications(
            bot=bot,
            poll_id=poll.id,
            render=render,
            session=session,
            pacing=0,
        ))

    assert session.query(Publication).count() == 0


def test_retry_after_is_retried(session: Session) -> None:
    poll = make_poll(session)
    publication_service.register_publication(
            poll_id=poll.id,
            inline_message_id='imid-1',
            session=session,
        )
    method = EditMessageText(inline_message_id='x', text='t')
    bot = FakeBot(errors={
            'imid-1': [
                TelegramRetryAfter(
                    method=method,
                    message='Too Many Requests',
                    retry_after=0,
                ),
            ],
        })

    asyncio.run(publication_updater.update_publications(
            bot=bot,
            poll_id=poll.id,
            render=render,
            session=session,
            pacing=0,
        ))

    assert len(bot.calls) == 2
    assert session.query(Publication).count() == 1


def test_enqueue_deduplicates_polls() -> None:
    publication_updater.enqueue_poll_update(1)
    publication_updater.enqueue_poll_update(1)
    publication_updater.enqueue_poll_update(2)

    assert publication_updater._update_queue.qsize() == 2


def test_enqueue_after_processing_adds_again() -> None:
    publication_updater.enqueue_poll_update(1)
    publication_updater._update_queue.get_nowait()
    publication_updater._pending_polls.discard(1)

    publication_updater.enqueue_poll_update(1)

    assert publication_updater._update_queue.qsize() == 1
