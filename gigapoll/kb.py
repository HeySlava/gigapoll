from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from gigapoll.enums import Modes


def get_different_modes_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ПЛЮС МИНУС', callback_data=Modes.PLUS_MINUS)
    return kb.as_markup()
