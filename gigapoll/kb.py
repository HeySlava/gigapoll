from textwrap import shorten
from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from gigapoll.button import CallbackButton
from gigapoll.data.models import Template
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
                text=b.button_name,
                callback_data=b.get_cbdata(),
            )
    kb.adjust(1)
    return kb.as_markup()


def get_publish_kb(
        templates: Sequence[Template],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in templates:
        text = f'{t.name} ->  {t.description}'
        wrapped = shorten(text, width=40, placeholder=' ...')
        kb.button(
                text=wrapped,
                switch_inline_query=str(t.id),
            )
    kb.adjust(1)
    return kb.as_markup()
