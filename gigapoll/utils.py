from aiogram import Bot
from aiogram.types.bot_command import BotCommand
from aiogram.utils.markdown import hbold

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

    text = description
    text = f'{text}\n\n'
    for choice, user_count_dict in d.items():
        text += f'{hbold(choice)}\n'
        for user, count in user_count_dict.items():
            text += f'  {user.inline_user_html} ({count} votes)\n'
    return text.strip()
