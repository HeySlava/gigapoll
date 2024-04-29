from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class CreateTemplate(StatesGroup):
    writing_name = State()
    writing_description = State()
    selecting_mode = State()
    writing_choices = State()


class PlusMinusChoices(StatesGroup):
    writing_positive_choice = State()
    writing_negative_choice = State()
