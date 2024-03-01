import os

from aiogram import Bot
from aiogram.enums import ParseMode

TOKEN = os.environ['POLL_TOKEN']

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
