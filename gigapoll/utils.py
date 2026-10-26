import logging
from textwrap import shorten
from typing import NamedTuple

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import InlineKeyboardMarkup
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import hbold

from gigapoll.data.models import Template
from gigapoll.dto import UserDTO
from gigapoll.dto import UserWithChoiceDTO
from gigapoll.enums import Commands

logger = logging.getLogger(__name__)


class CallbackReply(NamedTuple):
    text: str
    markup: InlineKeyboardMarkup


async def set_my_commands(bot: Bot) -> None:
    commands = [
            BotCommand(
                command=Commands.HELP,
                description='получить общую информацию',
            ),
            BotCommand(
                command=Commands.NEWTEMPLATE,
                description='создать новый шаблон',
            ),
            BotCommand(
                command=Commands.MYTEMPLATES,
                description='управление шаблонами',
            ),
        ]
    try:
        await bot.set_my_commands(commands=commands)
    except TelegramNetworkError:
        logger.warning(
            'Failed to set bot commands: network error (timeout)',
        )
    except Exception:
        logger.warning(
            'Failed to set bot commands', exc_info=True,
        )


def generate_poll_text(
        description: str,
        choices: list[UserWithChoiceDTO] = [],
) -> str:
    d: dict[str, dict[UserDTO, int]] = {}
    for b in choices:
        if b.choice not in d:
            d[b.choice] = {}
        if b.user not in d[b.choice]:
            d[b.choice][b.user] = 0
        d[b.choice][b.user] += 1

    lines = [f'{description}\n']
    for choice, user_count_dict in d.items():
        total_votes = sum(v for v in user_count_dict.values())
        vote_str = 'vote' if total_votes == 1 else 'votes'
        lines.append(f'{hbold(choice)} ({total_votes} {vote_str})')

        for index, (user, count) in enumerate(user_count_dict.items(), 1):
            text_line = f'  {index}. {user.inline_user_html}'
            if count > 1:
                text_line += f' ({count} votes)'
            lines.append(text_line)

        lines.append('')

    return '\n'.join(lines).strip()


def try_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return -1


def parse_poll_id_from_result_id(result_id: str) -> int | None:
    _, sep, tail = result_id.rpartition(':')
    if not sep:
        return None
    poll_id = try_int(tail)
    if poll_id < 0:
        return None
    return poll_id


def short_template_representation(template: Template) -> str:
    text = f'{template.name} -> {template.description}'
    wrapped = shorten(text, width=40, placeholder=' ...')
    return wrapped
