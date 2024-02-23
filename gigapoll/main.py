import asyncio
import os

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters import CommandObject
from aiogram.filters import CommandStart
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.utils.markdown import hbold
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from gigapoll import kb
from gigapoll.data import db_session
from gigapoll.data.models import Button
from gigapoll.data.models import Template
from gigapoll.dto import AggUsersByButton
from gigapoll.dto import ButtonDTO
from gigapoll.dto import CntPerValue
from gigapoll.dto import UserChoiceDTO
from gigapoll.enums import Modes
from gigapoll.services import buttons_service
from gigapoll.services import choice_service
from gigapoll.services import poll_service
from gigapoll.services import template_service
from gigapoll.states import CreateTemplate
from gigapoll.states import PlusMinusChoices
from gigapoll.utils import generate_poll_text
from gigapoll.utils import set_my_commands

TOKEN = os.environ['POLL_TOKEN']

dp = Dispatcher()


def _cnt_per_option_to_buttonDTO(
        cnt_per_option: list[CntPerValue],
        template: Template,
) -> list[ButtonDTO]:

    return [
            ButtonDTO(
                    description=template.description,
                    name=template.name,
                    button_name=dto.button_name,
                    button_cbdata=str(dto.button_cbdata),
                    votes=dto.cnt,
                )
            for dto
            in cnt_per_option
        ]


def _poll_choice_to_agg_user_per_button(
        all_choices: list[UserChoiceDTO],
) -> list[AggUsersByButton]:
    choice_models: dict[str, list[str]] = {}
    for uc_dto in all_choices:
        if uc_dto.choice not in choice_models:
            choice_models[uc_dto.choice] = []
        choice_models[uc_dto.choice].append(uc_dto.first_name)
    return [
            AggUsersByButton(
                button_value=k,
                users=v,
            )
            for k, v
            in choice_models.items()
        ]


@dp.message(CommandStart())
async def start_command(message: types.Message) -> None:
    if message.from_user:
        await message.answer(f'Hello, {hbold(message.from_user.full_name)}!')


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

    await state.update_data(mode=Modes.PLUS_MINUS)
    mode = cbdata_to_mode(cb.data)
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


async def save_plus_minus_choices(
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
    await save_plus_minus_choices(template.id, state, session)
    await state.clear()
    await message.answer('Шаблон сохранен')


@dp.message(Command('gigapoll'))
async def run_pull(
        message: Message,
        command: CommandObject,
) -> None:
    session = next(db_session.create_session())
    if not command.args:
        await message.reply('It cannot be empty')
        return

    if not message.from_user:
        return

    new_template_settings = template_service.get_new_template(
            user_id=message.from_user.id,
            template_name=command.args.strip(),
            session=session,
        )
    reply_markup = kb.get_poll_kb(new_template_settings)

    response_text = generate_poll_text(
            description=new_template_settings[0].description,
        )

    message_responce = await message.answer(
            response_text,
            reply_markup=reply_markup,
        )

    poll_service.resigter_poll(
            owner_id=message.from_user.id,
            message_id=message_responce.message_id,
            message_thread_id=message_responce.message_thread_id,
            chat_id=message_responce.chat.id,
            template_name=new_template_settings[0].name,
            session=session,
        )


@dp.callback_query()
async def user_choice_processing(cb: CallbackQuery) -> None:
    session = next(db_session.create_session())
    if not cb.data or not cb.message or not isinstance(cb.message, Message):
        return

    choice_service.add_choice(
            user_id=cb.from_user.id,
            message_id=cb.message.message_id,
            # message_thread_id=cb.message.message_thread_id,
            first_name=cb.from_user.first_name,
            last_name=cb.from_user.last_name,
            username=cb.from_user.username,
            chat_id=cb.message.chat.id,
            cbdata=cb.data,
            session=session,
        )

    template = template_service.get_template_by_cbdata(
            message_id=cb.message.message_id,
            chat_id=cb.message.chat.id,
            session=session,
        )

    cnt_per_option = choice_service.get_poll_choices_per_option(
            message_id=cb.message.message_id,
            chat_id=cb.message.chat.id,
            session=session,
        )

    all_choices = choice_service.get_all_poll_choices(
            message_id=cb.message.message_id,
            chat_id=cb.message.chat.id,
            session=session,
        )

    agg_users_per_value = _poll_choice_to_agg_user_per_button(all_choices)
    button_dtos = _cnt_per_option_to_buttonDTO(cnt_per_option, template)

    markup = kb.get_poll_kb(button_dtos)
    text = generate_poll_text(template.description, agg_users_per_value)

    await cb.message.edit_text(text=text)
    await cb.message.edit_reply_markup(reply_markup=markup)
    await cb.answer()


@dp.message(StateFilter(None))
async def echo_handler(message: Message) -> None:
    assert message.text

    await message.answer(text=message.text)


async def _main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
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
