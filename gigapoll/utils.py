from aiogram import Bot
from aiogram.utils.markdown import hbold

from gigapoll.dto import AggUsersByButton


async def set_my_commands(bot: Bot) -> None:
    from aiogram.types.bot_command import BotCommand
    commands = [
            BotCommand(command='start', description='bot information'),
            BotCommand(
                command='gigapoll',
                description='Start poll from user template',
            ),
            BotCommand(
                command='newtemplate',
                description='create a new poll template',
            ),
        ]
    await bot.set_my_commands(commands=commands)


def generate_poll_text(
        description: str,
        buttons: list[AggUsersByButton] = [],
) -> str:
    text = description
    text = f'{text}\n\n'
    for choice, users in buttons:
        text += f'{hbold(choice)}\n'
        formatted_users = [f'- {u}' for u in users]
        alligned_users = '\n'.join(formatted_users)
        text += alligned_users
        text = f'{text}\n\n'
    return text.strip()
