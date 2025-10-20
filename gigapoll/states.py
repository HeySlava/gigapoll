from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class CreateTemplate(StatesGroup):
    selecting_mode = State()
    processing_creation = State()
