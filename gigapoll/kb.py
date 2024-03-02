from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from gigapoll.button import CallbackButton
from gigapoll.enums import Modes


def get_different_modes_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ПЛЮС МИНУС', callback_data=Modes.PLUS_MINUS)
    return kb.as_markup()


def get_poll_kb(
        poll_buttons: list[CallbackButton],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for b in sorted(poll_buttons, key=lambda x: x.button_id):
        kb.button(
                text=b.get_public_name(),
                callback_data=b.get_cbdata(),
            )
    kb.adjust(1)
    return kb.as_markup()
