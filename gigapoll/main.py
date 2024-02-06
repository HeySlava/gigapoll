import asyncio
import os

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters import CommandObject
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from alembic import command
from alembic.config import Config

from gigapoll.data import db_session
from gigapoll.services import choice_service
from gigapoll.services import poll_service
from gigapoll.services import template_service
from gigapoll.utils import parse_template

# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.environ['POLL_TOKEN']

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


MODE_TO_CODE = {
        1: 'plus_minus',
    }


@dp.message(CommandStart())
async def start_command(message: types.Message) -> None:
    if message.from_user:
        await message.answer(f'Hello, {hbold(message.from_user.full_name)}!')


@dp.message(Command('new'))
async def new_template(
        message: Message,
        command: CommandObject,
) -> None:
    session = next(db_session.create_session())
    if not command.args:
        return message.reply('Пустой шаблон')

    try:
        conf = parse_template(command.args)
    except ValueError as e:
        return await message.reply(str(e))

    template_service.create_template(
            user_id=message.from_user.id,
            template_name=conf['name'],
            content=command.args,
            session=session,
        )
    await message.answer('gotovo')


def plus_minus_kb(
        poll_type: int,
        d: dict[str, int] = {},
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    keys = ('+', '-')
    for k in keys:
        if k not in d:
            d[k] = 0

    for k, v in d.items():
        text = f'{k} ({v} votes)'
        kb.button(text=text, callback_data=f'{poll_type}_{k}')
    kb.adjust(1)
    return kb.as_markup()


@dp.message(Command('gigapoll'))
async def run_pull(
        message: Message,
        command: CommandObject,
) -> None:
    session = next(db_session.create_session())
    if not command.args:
        return message.reply('It cannot be empty')

    if not message.from_user:
        return

    template = template_service.get_template(
            user_id=message.from_user.id,
            template_name=command.args.strip(),
            session=session,
        )

    message_responce = await message.answer(
            template.content,
            reply_markup=plus_minus_kb(1),
        )
    poll_service.resigter_poll(
            owner_id=message.from_user.id,
            message_id=message_responce.message_id,
            message_thread_id=message_responce.message_thread_id,
            chat_id=message_responce.chat.id,
            config=template.content,
            session=session,
        )


@dp.callback_query()
async def test_callback(cb: CallbackQuery) -> None:
    session = next(db_session.create_session())
    type_, choice = cb.data.split('_')
    assert cb.from_user
    assert cb.message
    choice_service.add_choice(
            user_id=cb.from_user.id,
            message_id=cb.message.message_id,
            message_thread_id=cb.message.message_thread_id,
            first_name=cb.from_user.first_name,
            last_name=cb.from_user.last_name,
            username=cb.from_user.username,
            chat_id=cb.message.chat.id,
            choice=choice,
            session=session,
        )
    d = choice_service.get_poll_choices(
            user_id=cb.from_user.id,
            message_id=cb.message.message_id,
            message_thread_id=cb.message.message_thread_id,
            chat_id=cb.message.chat.id,
            session=session,
        )
    await cb.message.edit_reply_markup(
            reply_markup=plus_minus_kb(int(type_), d),
        )
    await cb.answer()


@dp.message()
async def echo_handler(message: types.Message) -> None:
    try:
        await message.bot.send_message(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                text=message.text,
            )

    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer('Nice try!')


async def _main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


def setup_database() -> None:
    db_session.global_init()
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
