import asyncio
import contextlib
from typing import NamedTuple

from aiogram import Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineQuery
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.inline_query_result_article import InlineQueryResultArticle
from aiogram.types.input_text_message_content import InputTextMessageContent
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from gigapoll import kb
from gigapoll.bot import bot
from gigapoll.button import CallbackButton
from gigapoll.data import db_session
from gigapoll.data.models import Button
from gigapoll.data.models import Template
from gigapoll.enums import Commands
from gigapoll.enums import Modes
from gigapoll.filters import CallbackFloodControl
from gigapoll.filters import CallbackWithoutMessage
from gigapoll.services import buttons_service
from gigapoll.services import choice_service
from gigapoll.services import poll_service
from gigapoll.services import template_service
from gigapoll.states import CreateTemplate
from gigapoll.states import PlusMinusChoices
from gigapoll.utils import generate_poll_text
from gigapoll.utils import set_my_commands
from gigapoll.utils import try_int


dp = Dispatcher()


MSG_CHANGE_LIMIT_NUMBER = 15


class CallbackReply(NamedTuple):
    text: str
    markup: InlineKeyboardMarkup


@dp.message(Command(Commands.START))
@dp.message(Command(Commands.HELP))
async def start_command(message: Message) -> None:
    assert message.from_user
    msg = (
            'Это бот для создания голосовалок. Отличительная черта '
            'в том, что после нажания на кнопку, твой выбор сразу отображаетс'
            'я на экране'
            '\n\n'
            'Доступные команды'
            '\n'
            f'/{Commands.START}\n'
            f'/{Commands.HELP}\n'
            f'/{Commands.NEWTEMPLATE}\n'
            f'/{Commands.PUBLISH}'
            '\n\n'
            'Этот список команд должен отобраться внизу экрана под кнопкой'
            ' меню.'
            '\n\n'
            'P.S. в будущем добавится удобное меню для работы со своими '
            'шаблонами.'
        )

    await message.answer(msg)


@dp.message(Command('newtemplate'))
async def new_template(
        message: Message,
        state: FSMContext,
) -> None:
    await state.clear()
    await state.set_state(CreateTemplate.writing_name)
    await message.answer(
            'Введи название своего шаблона. '
            'Это техническое имя, с помощью которого ты '
            'будешь вызывать голосование'
        )


@dp.message(Command(Commands.PUBLISH))
async def handle_publish(
        message: Message,
        state: FSMContext,
) -> None:
    assert message.from_user

    session = next(db_session.create_session())

    await state.clear()
    templates = template_service.get_all_templates_for_user(
            message.from_user.id,
            session,
        )
    if templates:
        markup = kb.get_publish_kb(templates)
        await message.answer(
                text='Выбери шаблон для публикации',
                reply_markup=markup,
            )
    else:
        await message.answer(
                text='У тебя нет шаблонов для публикации',
            )


@dp.message(CreateTemplate.writing_name)
async def writing_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(CreateTemplate.writing_description)
    await message.answer(
            'Введи опасание. Этот текст будет видет '
            'пользователям при создании голосования'
        )


@dp.message(CreateTemplate.writing_description)
async def writing_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    text = 'Выбери режим голосования'
    await message.answer(text=text, reply_markup=kb.get_different_modes_kb())
    await state.set_state(CreateTemplate.selecting_mode)


async def _update_state_via_mode(
        mode: Modes,
        state: FSMContext,
) -> FSMContext:
    if mode == Modes.PLUS_MINUS:
        await state.set_state(PlusMinusChoices.writing_positive_choice)
    return state


def cbdata_to_mode(cbdata: str | None) -> Modes:
    if not cbdata:
        raise ValueError('Callback data could not be empty')
    return Modes(cbdata)


@dp.callback_query(CreateTemplate.selecting_mode)
async def selecting_mode(cb: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(cb.message, Message)

    mode = cbdata_to_mode(cb.data)
    await state.update_data(mode=mode)
    await _update_state_via_mode(mode, state)
    await cb.message.answer('Введи название кнопки для положительного ответа')
    await cb.answer()


@dp.message(PlusMinusChoices.writing_positive_choice)
async def writing_positive_choice(message: Message, state: FSMContext) -> None:
    await state.update_data(positive_choice=message.text)
    await state.set_state(PlusMinusChoices.writing_negative_choice)
    await message.answer('Введи название кнопки для негативного ответа')


async def create_plus_minus_template(
        message: Message,
        state: FSMContext,
        session: Session,
) -> Template:
    assert message.from_user

    user_data = await state.get_data()
    template = template_service.create_template(
            user_id=message.from_user.id,
            template_name=user_data['name'],
            description=user_data['description'],
            mode=user_data['mode'],
            session=session,
        )
    return template


async def save_plus_minus_buttons(
        template_id: int,
        state: FSMContext,
        session: Session,
) -> None:
    user_data = await state.get_data()
    positive_name = user_data['positive_choice']
    negative_name = user_data['negative_choice']

    positive_choice = Button(
            template_id=template_id,
            value=positive_name,
            is_positive=True,
        )

    negative_choice = Button(
            template_id=template_id,
            value=negative_name,
            is_negative=True,
        )
    buttons_service.add_choices(
            template_choices=[positive_choice, negative_choice],
            session=session,
        )


@dp.message(PlusMinusChoices.writing_negative_choice)
async def writing_negative_choice(message: Message, state: FSMContext) -> None:
    session = next(db_session.create_session())

    await state.update_data(negative_choice=message.text)
    template = await create_plus_minus_template(message, state, session)
    await save_plus_minus_buttons(template.id, state, session)
    await state.clear()
    await message.answer('Шаблон сохранен')


def save_choice_via_mode(
        cb: CallbackQuery,
        template: Template,
        session: Session,
) -> None:
    assert cb.data

    if template.mode == Modes.PLUS_MINUS:
        button_id, poll_id = CallbackButton.parse_cbdata(cb.data)
        choice_service.add_choice(
                user_id=cb.from_user.id,
                first_name=cb.from_user.first_name,
                last_name=cb.from_user.last_name,
                username=cb.from_user.username,
                poll_id=poll_id,
                button_id=button_id,
                session=session,
            )


async def handle_user_choice(
        cb: CallbackQuery,
        session: Session,
) -> CallbackReply:
    assert cb.data

    _, poll_id = CallbackButton.parse_cbdata(cb.data)
    template = template_service.get_template_by_poll_id(
            poll_id=poll_id,
            session=session,
        )

    save_choice_via_mode(cb, template, session)

    cnt_per_option = choice_service.get_poll_choices_per_option(
            template_id=template.id,
            poll_id=poll_id,
            session=session,
        )
    all_choices = choice_service.get_plus_minus_poll_choices(
            poll_id=poll_id,
            session=session,
        )

    for b in cnt_per_option:
        b.extend_button(poll_id)

    markup = kb.get_poll_kb(cnt_per_option)
    text = generate_poll_text(template.description, choices=all_choices)
    return CallbackReply(text, markup)


@dp.callback_query(CallbackFloodControl(MSG_CHANGE_LIMIT_NUMBER))
async def user_choice_processing(cb: CallbackQuery) -> None:
    session = next(db_session.create_session())

    reply = await handle_user_choice(cb=cb, session=session)
    with contextlib.suppress(TelegramBadRequest):
        await bot.edit_message_text(
                inline_message_id=cb.inline_message_id,
                text=reply.text,
                reply_markup=reply.markup,
                disable_web_page_preview=True,
            )
    await cb.answer()


@dp.inline_query(StateFilter(None))
async def start_poll_from_inline(inline_query: InlineQuery) -> None:
    session = next(db_session.create_session())

    try:
        t = template_service.get_template_by_id(
                user_id=inline_query.from_user.id,
                template_id=try_int(inline_query.query),
                session=session,
            )
    except NoResultFound:
        return

    poll = poll_service.resigter_poll(
            template_id=t.id,
            session=session,
        )

    poll_buttons = template_service.get_buttons_for_empty_poll(
            template_id=t.id,
            session=session,
        )

    for b in poll_buttons:
        b.extend_button(poll.id)

    result = [
            InlineQueryResultArticle(
                id=str(t.id),
                title=t.name,
                description=t.description,
                input_message_content=InputTextMessageContent(
                    message_text=t.description,
                    disable_web_page_preview=True,
                ),
                reply_markup=kb.get_poll_kb(poll_buttons),
            )
        ]
    await inline_query.answer(
            result,
            is_personal=True,
            cache_time=1,
        )


@dp.callback_query(CallbackWithoutMessage())
async def always_callback(cb: CallbackQuery) -> None:
    assert cb.data
    await cb.answer(
            text=(
                'Голос не учтён. '
                'Попробуй проголосовать через несколько секунд'
            ),
            show_alert=True,
        )


async def _main() -> None:
    await set_my_commands(bot)
    await dp.start_polling(bot)


def setup_database() -> None:
    db_session.global_init()
    # TODO: add params for alembic conf path
    alembic_cfg = Config('./alembic.ini')
    command.upgrade(alembic_cfg, 'head')
    engine = db_session.global_init()
    with engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, 'head')


def main() -> None:
    setup_database()
    asyncio.run(_main())


if __name__ == '__main__':
    main()
