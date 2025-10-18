from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class CreateTemplate(StatesGroup):
    writing_name = State()
    writing_description = State()
    selecting_mode = State()
    processing_creation = State()
