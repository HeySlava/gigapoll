import asyncio
import contextlib
from typing import NamedTuple
from typing import Tuple

from aiogram import Dispatcher
from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
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
from gigapoll.enums import Prefix
from gigapoll.exc import StrategyFinishedError
from gigapoll.filters import CallbackFilterByPrefix
from gigapoll.filters import CallbackFloodControl
from gigapoll.filters import CallbackTemplateManager
from gigapoll.services import buttons_service
from gigapoll.services import choice_service
from gigapoll.services import poll_service
from gigapoll.services import template_service
from gigapoll.states import CreateTemplate
from gigapoll.template_creation.strategies import STRATEGY_REGISTRY
from gigapoll.template_creation.strategies import TemplateCreationStrategy
from gigapoll.utils import generate_poll_text
from gigapoll.utils import set_my_commands
from gigapoll.utils import short_template_representation


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
            'Доступные команды:'
            '\n'
            f' /{Commands.HELP}\n'
            f' /{Commands.NEWTEMPLATE}\n'
            f' /{Commands.MYTEMPLATES}\n'
            '\n'
            'Этот список команд должен отобраться внизу экрана под кнопкой'
            ' меню.'
        )

    await message.answer(msg)


@dp.message(Command(Commands.NEWTEMPLATE))
async def new_template(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CreateTemplate.selecting_mode)
    await message.answer(
        'Выбери режим голосования',
        reply_markup=kb.get_different_modes_kb()
    )


async def my_templates(
        user_id: int,
) -> Tuple[str, InlineKeyboardMarkup]:
    session = next(db_session.create_session())

    templates = template_service.get_all_templates_for_user(
            user_id,
            session,
        )

    if not templates:
        text = 'Нет доступных шаблонов'
    else:
        text = 'Менеджер управления шаблонами'
    markup = kb.list_templates_to_manage(templates)
    return text, markup


@dp.message(Command(Commands.MYTEMPLATES))
async def handle_template_manager_command(
        message: Message,
        state: FSMContext,
) -> None:
    text, markup = await my_templates(message.from_user.id)
    await message.answer(text=text, reply_markup=markup)


@dp.callback_query(CallbackTemplateManager())
async def handle_template_manager_cb(
        cb: CallbackQuery,
        state: FSMContext,
) -> None:
    text, markup = await my_templates(cb.message.chat.id)
    await cb.message.edit_text(
            text=text,
            reply_markup=markup,
        )
    await cb.answer()


@dp.callback_query(
        CallbackFilterByPrefix(Prefix.VOTE),
        CallbackFloodControl(MSG_CHANGE_LIMIT_NUMBER),
    )
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


@dp.callback_query(
        CallbackFilterByPrefix(Prefix.VOTE),
    )
async def vote_not_saved(cb: CallbackQuery) -> None:
    assert cb.data
    await cb.answer(
            text=(
                'Голос не учтён. '
                'Попробуй проголосовать через несколько секунд'
            ),
            show_alert=True,
        )


@dp.callback_query(CallbackFilterByPrefix(Prefix.MANAGER_LIST))
async def select_template_to_manage(
        cb: CallbackQuery,
        state: FSMContext,
) -> None:
    assert cb.data
    session = next(db_session.create_session())
    _, template_id = cb.data.split(':')
    template_id = int(template_id)
    template = template_service.get_template_by_id(
            user_id=cb.from_user.id,
            template_id=template_id,
            session=session,
        )
    markup = kb.template_manager_markup(template)

    await cb.message.edit_text(
            text=short_template_representation(template),
            reply_markup=markup,
        )
    await cb.answer()


@dp.callback_query(CallbackFilterByPrefix(Prefix.DELETE_TEMPLATE))
async def delete_template(cb: CallbackQuery, state: FSMContext) -> None:
    assert cb.data
    session = next(db_session.create_session())
    _, _, template_id = cb.data.partition(':')

    templates = template_service.get_all_templates_for_user(
            user_id=cb.message.chat.id,
            session=session,
        )
    template = [t for t in templates if t.id == int(template_id)][0]
    templates = [t for t in templates if t.id != template.id]

    template_service.delete_user_template(
            template_id=template.id,
            user_id=template.user_id,
            session=session,
        )

    markup = kb.list_templates_to_manage(templates)

    await cb.message.edit_text(
            'Менеджер управления шаблонами',
            reply_markup=markup,
        )
    await cb.answer()


def cbdata_to_mode(cbdata: str | None) -> Modes:
    if not cbdata:
        raise ValueError('Callback data could not be empty')
    return Modes(cbdata)


@dp.callback_query(CreateTemplate.selecting_mode)
async def selecting_mode(cb: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(cb.message, Message)

    mode = cbdata_to_mode(cb.data)
    StrategyClass = STRATEGY_REGISTRY[mode]
    strategy_instance = StrategyClass(state)

    await state.update_data(mode=mode, strategy=strategy_instance)
    await state.set_state(CreateTemplate.processing_creation)

    first_question = await strategy_instance.get_next_question()
    await cb.message.answer(
        first_question,
        reply_markup=kb.get_creation_nav_kb(),
    )

    await cb.answer()


@dp.message(CreateTemplate.processing_creation)
async def process_creation_step(message: Message, state: FSMContext) -> None:
    session = next(db_session.create_session())
    user_data = await state.get_data()
    strategy: TemplateCreationStrategy = user_data['strategy']
    answer_text = message.text
    assert answer_text
    assert message.from_user

    try:
        await strategy.process_answer(answer_text)
    except ValueError as e:
        await message.answer(
            str(e),
            reply_markup=kb.get_creation_nav_kb(),
        )
        return

    try:
        next_question = await strategy.get_next_question()

        await message.answer(
            next_question,
            reply_markup=kb.get_creation_nav_kb(),
        )

    except StrategyFinishedError:
        try:
            await strategy.save_template(
                user_id=message.from_user.id,
                session=session,
            )
            await message.answer('Шаблон успешно сохранен!')
            await state.clear()

            text, markup = await my_templates(message.from_user.id)
            await message.answer(text=text, reply_markup=markup)

        except Exception as e:
            await message.answer(f'Не удалось сохранить шаблон: {e}')
            await state.clear()


@dp.callback_query(
    F.data == 'creation:cancel',
    CreateTemplate.processing_creation
)
async def cancel_creation(cb: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(cb.message, Message)
    await state.clear()
    await cb.message.edit_text('Создание шаблона отменено.')
    await cb.answer()


@dp.callback_query(
    F.data == 'creation:back',
    CreateTemplate.processing_creation
)
async def back_creation_step(cb: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(cb.message, Message)
    user_data = await state.get_data()
    strategy: TemplateCreationStrategy = user_data['strategy']

    can_go_back = await strategy.go_back()

    if can_go_back:
        prev_question = await strategy.get_next_question()
        await cb.message.edit_text(
            prev_question,
            reply_markup=kb.get_creation_nav_kb()
        )
    else:
        await state.set_state(CreateTemplate.selecting_mode)
        await cb.message.edit_text(
            'Выбери режим голосования',
            reply_markup=kb.get_different_modes_kb(),
        )

    await cb.answer()


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


@dp.inline_query()
async def start_poll_from_inline(inline_query: InlineQuery) -> None:
    session = next(db_session.create_session())

    try:
        templates = template_service.get_available_templates_by_name_like(
                user_id=inline_query.from_user.id,
                template_name=inline_query.query,
                session=session,
            )
    except (NoResultFound, ValueError):
        return

    result = []
    for t in templates:

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

        result.append(
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
            )
    await inline_query.answer(
            result,
            is_personal=True,
            cache_time=1,
        )


@dp.callback_query()
async def old_poll_response(cb: CallbackQuery) -> None:
    assert cb.data

    with contextlib.suppress(TelegramBadRequest):
        await bot.edit_message_reply_markup(
                inline_message_id=cb.inline_message_id,
                reply_markup=None,
            )
    await cb.answer()


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
