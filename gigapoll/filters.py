from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

from gigapoll.button import CallbackButton
from gigapoll.data import db_session
from gigapoll.enums import Commands
from gigapoll.enums import Prefix
from gigapoll.services import choice_service


class CallbackWithoutMessage(BaseFilter):
    async def __call__(self, cb: CallbackQuery) -> bool:
        if not cb.message:
            return True
        return False


class CallbackVotingWithAnyState(BaseFilter):
    async def __call__(self, cb: CallbackQuery) -> bool:
        if not cb.data:
            return False
        try:
            CallbackButton.parse_cbdata(cb.data)
        except Exception:
            return False
        else:
            return True


class CallbackFloodControl(BaseFilter):
    def __init__(self, msg_number: int) -> None:
        self.msg_number = msg_number

    async def __call__(self, cb: CallbackQuery) -> bool:
        assert cb.data
        _, poll_id = CallbackButton.parse_cbdata(cb.data)
        session = next(db_session.create_session())
        votes_number_for_poll = choice_service.get_number_of_choice(
                poll_id,
                session=session,
            )

        if votes_number_for_poll >= self.msg_number:
            return False
        return True


class CallbackTemplateManager(BaseFilter):
    async def __call__(self, cb: CallbackQuery) -> bool:
        assert cb.data
        return cb.data == Commands.MYTEMPLATES


class CallbackFilterByPrefix(BaseFilter):
    def __init__(self, prefix: Prefix) -> None:
        self.prefix = prefix

    async def __call__(self, cb: CallbackQuery) -> bool:
        assert cb.data
        return cb.data.startswith(self.prefix)
