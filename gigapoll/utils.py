from textwrap import shorten

from aiogram import Bot
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import hbold

from gigapoll.data.models import Template
from gigapoll.dto import UserDTO
from gigapoll.dto import UserWithChoiceDTO
from gigapoll.enums import Commands


async def set_my_commands(bot: Bot) -> None:
    commands = [
            BotCommand(
                command=Commands.START,
                description='получить общую информацию',
            ),
            BotCommand(
                command=Commands.HELP,
                description='получить общую информацию',
            ),
            BotCommand(
                command=Commands.PUBLISH,
                description='опубликовать твое голосование',
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
    await bot.set_my_commands(commands=commands)


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


def short_template_representation(template: Template) -> str:
    text = f'{template.name} -> {template.description}'
    wrapped = shorten(text, width=40, placeholder=' ...')
    return wrapped
