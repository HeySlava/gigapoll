import asyncio
import contextlib
import logging
from collections.abc import Callable

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.exceptions import TelegramBadRequest
from aiogram.exceptions import TelegramNetworkError
from aiogram.exceptions import TelegramRetryAfter
from sqlalchemy.orm import Session

from gigapoll.data import db_session
from gigapoll.services import publication_service
from gigapoll.utils import CallbackReply

logger = logging.getLogger(__name__)

EDIT_PACING_SECONDS = 0.05

RenderFunc = Callable[[int, Session], CallbackReply]

_pending_polls: set[int] = set()
_update_queue: asyncio.Queue[int] = asyncio.Queue()


def enqueue_poll_update(poll_id: int) -> None:
    if poll_id in _pending_polls:
        return
    _pending_polls.add(poll_id)
    _update_queue.put_nowait(poll_id)


async def _safe_edit(
        bot: Bot,
        inline_message_id: str,
        reply: CallbackReply,
) -> None:
    await bot.edit_message_text(
            inline_message_id=inline_message_id,
            text=reply.text,
            reply_markup=reply.markup,
            disable_web_page_preview=True,
        )


async def edit_publication(
        bot: Bot,
        inline_message_id: str,
        reply: CallbackReply,
        session: Session,
) -> None:
    try:
        await _safe_edit(bot, inline_message_id, reply)
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        with contextlib.suppress(TelegramAPIError):
            await _safe_edit(bot, inline_message_id, reply)
    except TelegramBadRequest as e:
        if 'message is not modified' in str(e):
            return
        logger.info(
                'Removing dead publication %s: %s',
                inline_message_id,
                e,
            )
        publication_service.delete_publication(
                inline_message_id=inline_message_id,
                session=session,
            )
    except TelegramNetworkError:
        logger.warning(
                'Network error while editing %s',
                inline_message_id,
            )


async def update_publications(
        bot: Bot,
        poll_id: int,
        render: RenderFunc,
        session: Session,
        pacing: float = EDIT_PACING_SECONDS,
) -> None:
    reply = render(poll_id, session)
    publications = publication_service.get_poll_publications(
            poll_id=poll_id,
            session=session,
        )
    for pub in publications:
        await edit_publication(bot, pub.inline_message_id, reply, session)
        await asyncio.sleep(pacing)


async def run_worker(bot: Bot, render: RenderFunc) -> None:
    while True:
        poll_id = await _update_queue.get()
        _pending_polls.discard(poll_id)
        session = next(db_session.create_session())
        try:
            await update_publications(bot, poll_id, render, session)
        except Exception:
            logger.exception(
                    'Failed to update publications for poll %s',
                    poll_id,
                )
