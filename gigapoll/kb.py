from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from gigapoll.dto import ButtonDTO
from gigapoll.enums import Modes


def get_different_modes_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ПЛЮС МИНУС', callback_data=Modes.PLUS_MINUS)
    return kb.as_markup()


def get_poll_kb(
        template_settings: list[ButtonDTO],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in template_settings:
        kb.button(
                text=s.public_name,
                callback_data=s.button_cbdata,
            )
    kb.adjust(1)
    return kb.as_markup()
