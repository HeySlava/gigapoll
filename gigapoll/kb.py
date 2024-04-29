from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from gigapoll.button import CallbackButton
from gigapoll.data.models import Template
from gigapoll.enums import Commands
from gigapoll.enums import Modes
from gigapoll.enums import Prefix
from gigapoll.utils import short_template_representation


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
        text = short_template_representation(t)
        kb.button(
                text=text,
                switch_inline_query=str(t.id),
            )
    kb.adjust(1)
    return kb.as_markup()


def list_templates_to_manage(
        templates: Sequence[Template],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in templates:
        text = short_template_representation(t)
        kb.button(
                text=text,
                callback_data=f'{Prefix.MANAGER_LIST}:{str(t.id)}',
            )
    kb.adjust(1)
    return kb.as_markup()


def template_manager_markup(
        template: Template,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
            text='Опубликовать шаблон',
            switch_inline_query=str(template.id),
        )
    kb.button(
            text='Удалить шаблон',
            callback_data=f'{Prefix.DELETE_TEMPLATE}:{template.id}',
        )
    kb.button(
            text='Назад',
            callback_data=Commands.MYTEMPLATES,
        )
    kb.adjust(1)
    return kb.as_markup()
