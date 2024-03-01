from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery


class CallbackWithoutMessage(BaseFilter):
    async def __call__(self, cb: CallbackQuery) -> bool:
        if not cb.message:
            return True
        return False
