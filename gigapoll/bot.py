import os

import aiohttp
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

TOKEN = os.environ['POLL_TOKEN']

session = AiohttpSession(timeout=aiohttp.ClientTimeout(total=60))
bot = Bot(TOKEN, parse_mode=ParseMode.HTML, session=session)
